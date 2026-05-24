import os
import io
import base64
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, render_template, request, session, jsonify
from werkzeug.utils import secure_filename
from sklearn.model_selection import train_test_split
from sklearn.ensemble import (RandomForestClassifier, GradientBoostingClassifier,
                               AdaBoostClassifier, BaggingClassifier)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix,
                              precision_score, recall_score, f1_score)
from sklearn.preprocessing import LabelEncoder

# ─────────────────────────────────────────
# App Config
# ─────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "ids_secret_key_2024"
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'csv'}

KDD_COLUMNS = [
    'duration','protocol_type','service','flag','src_bytes','dst_bytes',
    'land','wrong_fragment','urgent','hot','num_failed_logins','logged_in',
    'num_compromised','root_shell','su_attempted','num_root','num_file_creations',
    'num_shells','num_access_files','num_outbound_cmds','is_host_login',
    'is_guest_login','count','srv_count','serror_rate','srv_serror_rate',
    'rerror_rate','srv_rerror_rate','same_srv_rate','diff_srv_rate',
    'srv_diff_host_rate','dst_host_count','dst_host_srv_count',
    'dst_host_same_srv_rate','dst_host_diff_srv_rate','dst_host_same_src_port_rate',
    'dst_host_srv_diff_host_rate','dst_host_serror_rate','dst_host_srv_serror_rate',
    'label'
]

# Global in-memory store (per server process)
model_store = {}

ALGORITHMS = {
    '1': ('Logistic Regression',  LogisticRegression(max_iter=1000)),
    '2': ('Random Forest',         RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)),
    '3': ('AdaBoost',              AdaBoostClassifier(n_estimators=50, random_state=42)),
    '4': ('Bagging',               BaggingClassifier(n_estimators=50, random_state=42)),
    '5': ('Gradient Boosting',     GradientBoostingClassifier(n_estimators=100, random_state=42)),
}

# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def load_dataset(filepath):
    df = pd.read_csv(filepath, header=None, low_memory=False)
    n_features = df.shape[1] - 1
    feat_names = KDD_COLUMNS[:n_features] if n_features <= len(KDD_COLUMNS) - 1 \
                 else [f'f{i}' for i in range(n_features)]
    df.columns = feat_names + ['label']
    df = df[~df['label'].astype(str).str.lower().isin(['criminal', 'label', 'attack_type'])]
    return df.reset_index(drop=True)


def preprocess(df):
    df = df.copy().fillna(0)
    le = LabelEncoder()
    for col in df.select_dtypes(include='object').columns:
        if col != 'label':
            df[col] = le.fit_transform(df[col].astype(str))
    df['label'] = df['label'].apply(
        lambda x: 0 if str(x).strip().lower() in ['0', 'normal'] else 1
    )
    X = df.drop('label', axis=1)
    y = df['label']
    return X, y


def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=120)
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img


def make_cm_chart(cm, alg_name):
    fig, ax = plt.subplots(figsize=(5, 4))
    fig.patch.set_facecolor('white')
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=['Normal', 'Attack'],
                yticklabels=['Normal', 'Attack'],
                linewidths=0.5, linecolor='#e5e7eb')
    ax.set_title(f'Confusion Matrix — {alg_name}', fontsize=12, fontweight='bold', pad=12)
    ax.set_ylabel('Actual', fontsize=11)
    ax.set_xlabel('Predicted', fontsize=11)
    fig.tight_layout()
    return fig_to_b64(fig)


def make_accuracy_chart(results):
    names  = list(results.keys())
    scores = [results[n] if isinstance(results[n], (int, float))
              else results[n]['acc'] for n in names]
    colors = ['#ef4444', '#f97316', '#8b5cf6', '#3b82f6', '#10b981']
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('#f9fafb')
    bars = ax.bar(names, scores, color=colors, width=0.5,
                  edgecolor='white', linewidth=1.5, zorder=3)
    ax.set_ylim(50, 106)
    ax.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
    ax.set_title('Algorithm Accuracy Comparison — NSL-KDD Dataset',
                 fontsize=13, fontweight='bold', pad=14)
    ax.tick_params(axis='x', labelsize=11)
    ax.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    for bar, score in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{score}%', ha='center', va='bottom',
                fontsize=11, fontweight='bold')
    best_i = scores.index(max(scores))
    bars[best_i].set_edgecolor('#10b981')
    bars[best_i].set_linewidth(2.5)
    fig.tight_layout()
    return fig_to_b64(fig)


# ─────────────────────────────────────────
# Routes
# ─────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'csvfile' not in request.files:
            return render_template('upload.html', error='No file selected.')
        f = request.files['csvfile']
        if f.filename == '' or not allowed_file(f.filename):
            return render_template('upload.html', error='Please upload a valid .csv file.')
        filename = secure_filename(f.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(filepath)
        session['filepath'] = filepath
        # Clear previous splits and models
        for key in ['X_train','X_test','y_train','y_test','trained_model','last_alg']:
            model_store.pop(key, None)
        return render_template('upload.html',
                               success=f'"{filename}" uploaded successfully! Now view and split your data.')
    return render_template('upload.html')


@app.route('/view')
def view():
    filepath = session.get('filepath')
    if not filepath or not os.path.exists(filepath):
        return render_template('view.html',
                               error='No dataset uploaded yet. Please upload a CSV file first.')
    try:
        df = load_dataset(filepath)
        preview = df.head(10).to_html(
            classes='ids-table', border=0, index=False)
        stats = {
            'rows':   len(df),
            'cols':   df.shape[1],
            'normal': int((df['label'].astype(str).isin(['0','normal'])).sum()),
            'attack': int((~df['label'].astype(str).isin(['0','normal'])).sum()),
        }
        return render_template('view.html', table=preview, stats=stats)
    except Exception as e:
        return render_template('view.html', error=f'Error reading file: {str(e)}')


@app.route('/traintest', methods=['GET', 'POST'])
def traintest():
    filepath = session.get('filepath')
    if not filepath or not os.path.exists(filepath):
        return render_template('traintest.html',
                               error='No dataset uploaded yet. Please upload first.')
    if request.method == 'POST':
        try:
            test_size = float(request.form.get('test_size', 0.2))
            if not 0.1 <= test_size <= 0.4:
                raise ValueError('Test size must be between 0.1 and 0.4')
            df = load_dataset(filepath)
            X, y = preprocess(df)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y)
            model_store['X_train'] = X_train
            model_store['X_test']  = X_test
            model_store['y_train'] = y_train
            model_store['y_test']  = y_test
            # Clear any previously trained model
            model_store.pop('trained_model', None)
            model_store.pop('last_alg', None)
            return render_template('traintest.html',
                                   success=True,
                                   train_n=len(X_train),
                                   test_n=len(X_test),
                                   test_ratio=int(test_size * 100),
                                   train_preview=X_train.head(5).to_html(
                                       classes='ids-table', border=0, index=False),
                                   test_preview=X_test.head(5).to_html(
                                       classes='ids-table', border=0, index=False))
        except Exception as e:
            return render_template('traintest.html', error=str(e))
    return render_template('traintest.html')


@app.route('/modelperformance', methods=['GET', 'POST'])
def modelperformance():
    if request.method == 'POST':
        if 'X_train' not in model_store:
            return render_template('modelperformance.html',
                                   error='Please split the dataset first before training.')
        alg_id = request.form.get('algorithm', '2')
        if alg_id not in ALGORITHMS:
            return render_template('modelperformance.html',
                                   error='Invalid algorithm selected.')
        try:
            alg_name, mdl = ALGORITHMS[alg_id]
            X_train = model_store['X_train']
            X_test  = model_store['X_test']
            y_train = model_store['y_train']
            y_test  = model_store['y_test']
            mdl.fit(X_train, y_train)
            y_pred  = mdl.predict(X_test)
            acc  = round(accuracy_score(y_test, y_pred) * 100, 2)
            prec = round(precision_score(y_test, y_pred, zero_division=0) * 100, 2)
            rec  = round(recall_score(y_test, y_pred, zero_division=0) * 100, 2)
            f1   = round(f1_score(y_test, y_pred, zero_division=0) * 100, 2)
            cm   = confusion_matrix(y_test, y_pred)
            model_store['trained_model'] = mdl
            model_store['last_alg']      = alg_name
            return render_template('modelperformance.html',
                                   alg_name=alg_name,
                                   acc=acc, prec=prec, rec=rec, f1=f1,
                                   cm_img=make_cm_chart(cm, alg_name),
                                   success=True)
        except Exception as e:
            return render_template('modelperformance.html',
                                   error=f'Training error: {str(e)}')
    return render_template('modelperformance.html')


@app.route('/graph')
def graph():
    if 'X_train' not in model_store:
        return render_template('graph.html',
                               error='Please upload a dataset and split it first.')
    try:
        X_train = model_store['X_train']
        X_test  = model_store['X_test']
        y_train = model_store['y_train']
        y_test  = model_store['y_test']
        results = {}
        for aid, (name, mdl) in ALGORITHMS.items():
            mdl.fit(X_train, y_train)
            results[name] = round(
                accuracy_score(y_test, mdl.predict(X_test)) * 100, 2)
        chart_img = make_accuracy_chart(results)
        return render_template('graph.html',
                               chart_img=chart_img, results=results)
    except Exception as e:
        return render_template('graph.html',
                               error=f'Error generating chart: {str(e)}')


@app.route('/compare')
def compare():
    if 'X_train' not in model_store:
        return render_template('compare.html',
                               error='Please upload a dataset and split it first.')
    try:
        X_train = model_store['X_train']
        X_test  = model_store['X_test']
        y_train = model_store['y_train']
        y_test  = model_store['y_test']

        rows    = []
        cm_imgs = {}

        for aid, (name, mdl) in ALGORITHMS.items():
            mdl.fit(X_train, y_train)
            y_pred = mdl.predict(X_test)
            acc  = round(accuracy_score(y_test, y_pred) * 100, 2)
            prec = round(precision_score(y_test, y_pred, zero_division=0) * 100, 2)
            rec  = round(recall_score(y_test, y_pred, zero_division=0) * 100, 2)
            f1   = round(f1_score(y_test, y_pred, zero_division=0) * 100, 2)
            cm   = confusion_matrix(y_test, y_pred)
            rows.append({'name': name, 'acc': acc, 'prec': prec, 'rec': rec, 'f1': f1})
            cm_imgs[name] = make_cm_chart(cm, name)

        rows.sort(key=lambda x: x['acc'], reverse=True)

        best = {
            'acc':  max(r['acc']  for r in rows),
            'prec': max(r['prec'] for r in rows),
            'rec':  max(r['rec']  for r in rows),
            'f1':   max(r['f1']   for r in rows),
        }

        # Multi-metric bar chart
        names      = [r['name'] for r in rows]
        x          = np.arange(len(names))
        width      = 0.18
        m_colors   = ['#1a56db', '#10b981', '#f97316', '#ef4444']
        m_labels   = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
        m_keys     = ['acc', 'prec', 'rec', 'f1']

        fig, ax = plt.subplots(figsize=(13, 6))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('#f9fafb')
        for i, (mkey, mc, ml) in enumerate(zip(m_keys, m_colors, m_labels)):
            vals = [r[mkey] for r in rows]
            ax.bar(x + i*width - 1.5*width, vals, width,
                   label=ml, color=mc, alpha=0.85,
                   edgecolor='white', linewidth=0.8, zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels(names, fontsize=11)
        ax.set_ylim(50, 112)
        ax.set_ylabel('Score (%)', fontsize=12, fontweight='bold')
        ax.set_title('All Algorithms — Full Metrics Comparison',
                     fontsize=13, fontweight='bold', pad=14)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', linestyle='--', alpha=0.4, zorder=0)
        ax.set_axisbelow(True)
        ax.legend(frameon=True, fontsize=11, loc='lower right')
        fig.tight_layout()
        bar_img = fig_to_b64(fig)

        return render_template('compare.html',
                               rows=rows, best=best,
                               cm_imgs=cm_imgs,
                               bar_img=bar_img)
    except Exception as e:
        return render_template('compare.html',
                               error=f'Error: {str(e)}')


@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    if request.method == 'POST':
        raw = request.form.get('features', '').strip()
        if not raw:
            return render_template('prediction.html',
                                   error='Please enter feature values or click a row from the table.')
        try:
            values = [float(v.strip()) for v in raw.split(',')]
            if len(values) != 38:
                return render_template('prediction.html',
                                       error=f'Expected 38 feature values, got {len(values)}. '
                                             f'Click a row from the table above to auto-fill.')
            if 'trained_model' not in model_store:
                # Train RF on full dataset automatically
                filepath = session.get('filepath')
                if not filepath or not os.path.exists(filepath):
                    return render_template('prediction.html',
                                           error='No model trained yet. Please upload a dataset, '
                                                 'split it and run Model Performance first.')
                df = load_dataset(filepath)
                X, y = preprocess(df)
                mdl = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)
                mdl.fit(X, y)
                model_store['trained_model'] = mdl
                model_store['last_alg']      = 'Random Forest'

            model  = model_store['trained_model']
            pred   = model.predict([values])[0]
            proba  = model.predict_proba([values])[0] \
                     if hasattr(model, 'predict_proba') else None
            label  = 'Attack Detected' if pred == 1 else 'Normal Traffic'
            badge  = 'danger' if pred == 1 else 'success'
            conf   = round(max(proba) * 100, 2) if proba is not None else None
            return render_template('prediction.html',
                                   result=label, badge=badge, conf=conf,
                                   alg=model_store.get('last_alg', 'Random Forest'),
                                   features_input=raw,
                                   success=True)
        except ValueError as e:
            return render_template('prediction.html',
                                   error=f'Invalid input — {str(e)}. '
                                         f'Make sure all values are numbers.')
    return render_template('prediction.html')


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)

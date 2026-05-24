# 🔐 Cloud-Based Intrusion Detection System Using ML Techniques

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.3%2B-lightgrey)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.2%2B-orange)
![Dataset](https://img.shields.io/badge/Dataset-NSL--KDD-green)
![Accuracy](https://img.shields.io/badge/Accuracy-98.71%25-brightgreen)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

> **Published in IJSREM — May 2024**
> Authors: Manikrao Mulge, Neha, Namratha, Prerana, **Sandhya Rani**

---

## 📌 Overview

A machine learning-based **Intrusion Detection System (IDS)** that monitors cloud network
traffic and detects anomalous (malicious) behaviour. The system uses the **NSL-KDD dataset**
and benchmarks five classification algorithms, with **Random Forest** achieving the best results.

---

## 🎯 Problem Statement

Traditional firewalls and rule-based security systems cannot detect unknown or zero-day attacks.
This IDS learns from historical network traffic patterns and classifies traffic as:

- **Normal** — legitimate network activity
- **Attack** — DoS, Probe, R2L, or U2R attack

---

## 📊 Results

| Algorithm           | Accuracy |
|---------------------|----------|
| **Random Forest**   | **98.71%** |
| Bagging             | 98.67%   |
| Gradient Boosting   | 97.34%   |
| AdaBoost            | 93.24%   |
| Logistic Regression | 83.54%   |

> Results are generated dynamically from your uploaded dataset.

---

## 🧰 Tech Stack

| Category        | Tools                                    |
|-----------------|------------------------------------------|
| Language        | Python 3.8+                              |
| Backend         | Flask 2.3+                               |
| ML Framework    | scikit-learn                             |
| Data Processing | pandas, NumPy                            |
| Visualisation   | matplotlib, seaborn                      |
| Frontend        | Bootstrap 3, Chart.js, Font Awesome      |
| Dataset         | NSL-KDD (KDDTest1.csv / KDDTrain+.csv)   |

---

## 📁 Project Structure

```
intrusion-detection-system/
│
├── app.py                    ← Main Flask application (all routes + ML logic)
├── requirements.txt          ← Python dependencies
├── README.md
│
├── dataset/
│   └── KDDTest1.csv          ← NSL-KDD dataset (22 542 records)
│
├── uploads/                  ← User-uploaded CSV files (auto-created)
│
├── templates/
│   ├── base.html             ← Shared layout (navbar, footer)
│   ├── index.html            ← Home page
│   ├── upload.html           ← Upload dataset
│   ├── view.html             ← View dataset
│   ├── traintest.html        ← Train/test split
│   ├── modelperformance.html ← Train model + metrics + confusion matrix
│   ├── graph.html            ← Algorithm accuracy comparison chart
│   └── prediction.html       ← Live attack prediction
│
└── static/
    ├── css/
    │   ├── ids.css           ← Custom professional stylesheet
    │   └── bootstrap.min.css
    ├── js/
    │   ├── jquery.js
    │   ├── bootstrap.min.js
    │   └── chart/Chart.min.js
    ├── fonts/                ← Font Awesome + Roboto fonts
    └── images/
        └── IDS.jpg
```

---

## ⚙️ Installation & Running

### Prerequisites
- Python 3.8 or higher
- pip

### Step 1 — Clone / Download
```bash
git clone https://github.com/sandhyarani-cse/intrusion-detection-system.git
cd IDS_Project
```

### Step 2 — Create a virtual environment (recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Run the application
```bash
python app.py
```

### Step 5 — Open in browser
```
http://127.0.0.1:5000
```

---

## 🚀 Usage Guide

1. **Home** — Read the project overview and algorithm comparison table.
2. **Upload Dataset** — Upload `dataset/KDDTest1.csv` (or any NSL-KDD CSV).
3. **View Dataset** — Inspect the first 10 records and class distribution.
4. **Train / Test** — Choose a test-set ratio (10–40%) and split the data.
5. **Model Performance** — Select an algorithm → train → view Accuracy, Precision, Recall, F1, and a live confusion matrix plot.
6. **Graph** — Auto-trains all 5 algorithms and renders a comparison bar chart.
7. **Prediction** — Paste 38 comma-separated feature values to classify a single network record.

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `No dataset uploaded` | Upload a CSV via the Upload page first |
| `Please split dataset first` | Go to Train/Test page and split before training |
| Port 5000 already in use | Change port: `app.run(port=5001)` in `app.py` |
| CSV not accepted | Ensure the file has 38 numeric features + 1 label column |

---

## 📄 Publication

> Mulge M., Neha, Namratha, Prerana, **Sandhya Rani** —
> *"Cloud-Based Data Intrusion Detection System Using ML Techniques"*,
> IJSREM, May 2024.

---

## 📜 License
MIT License — free to use and adapt with attribution.

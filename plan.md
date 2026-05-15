# Phishing Website Detection — Project Plan

## Project Overview

**Goal**: Build a machine learning system that detects phishing websites based on URL structure and webpage features with high accuracy (target ≥ 98%).

**Stack**: Python · scikit-learn · XGBoost · FastAPI · MongoDB · Docker · Pandas · NumPy

---

## Directory Structure

```
phishing-detection/
├── data/
│   ├── raw/                        # Downloaded datasets (never touch)
│   │   ├── phiusiil_uci.csv
│   │   ├── uci_classic.csv
│   │   └── zenodo_domain.json
│   ├── processed/                  # Cleaned, merged, feature-engineered data
│   │   ├── train.csv
│   │   ├── val.csv
│   │   └── test.csv
│   └── interim/                    # Mid-pipeline scratch data
│
├── notebooks/
│   ├── 01_eda.ipynb                # Exploratory Data Analysis
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model_training.ipynb
│   ├── 04_model_evaluation.ipynb
│   └── 05_ensemble_stacking.ipynb
│
├── src/
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py               # Dataset download + load
│   │   ├── cleaner.py              # Null handling, dedup, encoding
│   │   └── splitter.py             # Train/val/test split with stratification
│   │
│   ├── features/
│   │   ├── __init__.py
│   │   ├── url_features.py         # URL-based feature extraction
│   │   ├── content_features.py     # HTML/webpage feature extraction
│   │   └── selector.py             # RFECV / SelectKBest feature selection
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── baseline.py             # Logistic Regression, RF baselines
│   │   ├── boosting.py             # XGBoost / LightGBM
│   │   ├── neural.py               # DNN / CNN
│   │   └── ensemble.py             # Stacked ensemble
│   │
│   ├── training/
│   │   ├── __init__.py
│   │   ├── trainer.py              # Main training loop
│   │   ├── tuner.py                # Optuna hyperparameter tuning
│   │   └── evaluator.py            # Metrics, confusion matrix, ROC-AUC
│   │
│   └── api/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app entry
│       ├── routes.py               # /predict and /batch endpoints
│       ├── schema.py               # Pydantic input/output models
│       └── middleware.py           # Auth, rate limiting, logging
│
├── models/
│   ├── saved/                      # Serialized .pkl / .joblib model files
│   └── reports/                    # Accuracy, F1, ROC-AUC reports per run
│
├── tests/
│   ├── test_features.py
│   ├── test_model.py
│   └── test_api.py
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── config/
│   └── config.yaml                 # All configurable params in one place
│
├── requirements.txt
├── .env.example
├── plan.md
├── model.md
└── design.md
```

---

## Phase Breakdown

### Phase 1 — Data Collection & Setup (Days 1–2)

- [ ] Download UCI PhiUSIIL dataset (`ucimlrepo` package, id=967)
- [ ] Download UCI Classic dataset (Kaggle or direct UCI link)
- [ ] Download Zenodo PhishTank+OpenPhish domain dataset
- [ ] Set up Python virtual environment
- [ ] Install all dependencies
- [ ] Initialize MongoDB for storing prediction logs
- [ ] Confirm dataset shapes and column names

### Phase 2 — EDA & Preprocessing (Days 3–4)

- [ ] Check class distribution (legitimate vs phishing ratio)
- [ ] Identify null values and outliers
- [ ] Plot feature correlation heatmaps
- [ ] Apply SMOTE to balance classes
- [ ] Normalize/standardize numerical features
- [ ] Encode categorical features (Label Encoding or One-Hot)
- [ ] Stratified train/val/test split (75% / 10% / 15%)

### Phase 3 — Feature Engineering (Days 5–6)

- [ ] Extract URL-based features from raw URLs (if not pre-extracted)
- [ ] Merge domain-level features from Zenodo dataset
- [ ] Apply RFECV to select top features
- [ ] Run SelectKBest as cross-validation
- [ ] Document final feature set in `model.md`

### Phase 4 — Model Training (Days 7–10)

- [ ] Train baseline models: Logistic Regression, Random Forest
- [ ] Train XGBoost with default params → evaluate
- [ ] Train LightGBM
- [ ] Train DNN (3-layer MLP with dropout)
- [ ] Hyperparameter tune top 2 models using Optuna
- [ ] Build stacked ensemble (best models as base, LR as meta)
- [ ] Evaluate all models on test set

### Phase 5 — API & Deployment (Days 11–13)

- [ ] Build FastAPI `/predict` endpoint (single URL)
- [ ] Build `/batch` endpoint (list of URLs)
- [ ] Add Pydantic validation schemas
- [ ] Log all predictions to MongoDB
- [ ] Containerize with Docker
- [ ] Write API tests

### Phase 6 — Final Evaluation & Docs (Days 14–15)

- [ ] Generate full classification report per model
- [ ] Plot ROC-AUC curves for all models
- [ ] Write final model card
- [ ] Clean up notebooks
- [ ] Finalize README

---

## Target Metrics

| Metric    | Minimum Target |
|-----------|---------------|
| Accuracy  | ≥ 98%         |
| Precision | ≥ 97%         |
| Recall    | ≥ 97%         |
| F1 Score  | ≥ 97%         |
| ROC-AUC   | ≥ 0.99        |
| FPR       | ≤ 2%          |

---

## Dataset Links

| Dataset | URL |
|---------|-----|
| UCI PhiUSIIL (Primary) | https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset |
| UCI Classic | https://archive.ics.uci.edu/dataset/327/phishing+websites |
| Zenodo PhishTank+OpenPhish | https://zenodo.org/records/8364668 |
| PhishTank API | https://phishtank.org/developer_info.php |
| OpenPhish Feed | https://openphish.com/phishing_feeds.html |

---

## Dependencies

```txt
# Core
python>=3.10
pandas
numpy
scikit-learn
xgboost
lightgbm
imbalanced-learn      # SMOTE
optuna                # Hyperparameter tuning
joblib

# Feature Extraction
tldextract
urllib3
beautifulsoup4
requests

# API
fastapi
uvicorn
pydantic
motor                 # Async MongoDB driver

# Database
pymongo

# Visualization
matplotlib
seaborn
plotly

# Notebooks
jupyter
ipykernel

# Testing
pytest
httpx

# Data Loading
ucimlrepo
```

---

## Environment Variables (.env)

```env
MONGO_URI=mongodb://localhost:27017
DB_NAME=phishing_detection
API_KEY=your_secret_api_key
MODEL_PATH=models/saved/best_model.joblib
LOG_LEVEL=INFO
```

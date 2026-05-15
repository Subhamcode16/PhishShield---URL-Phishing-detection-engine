# Phishing Website Detection — Model Documentation

## Overview

This document covers the complete ML pipeline: feature set, model architectures, training process, hyperparameter tuning, and evaluation strategy.

---

## Feature Set

### Category 1 — URL-Based Features (Extracted from raw URL string)

These require no external HTTP request — computed instantly from the URL string itself.

| Feature | Description | Phishing Signal |
|---------|-------------|-----------------|
| `url_length` | Total character count of URL | Long URLs = suspicious |
| `domain_length` | Character count of domain only | Abnormally long domains |
| `num_dots` | Number of dots in URL | More dots = obfuscation |
| `num_hyphens` | Number of hyphens in URL | Hyphens used in spoofing |
| `num_at_symbols` | Count of `@` in URL | Forces browser to ignore left part |
| `num_slashes` | Forward slash count | Deep paths = suspicious |
| `num_subdomains` | Subdomain depth count | `secure.paypal.evil.com` = 3 subdomains |
| `has_ip_address` | 1 if IP used instead of domain | Strong phishing indicator |
| `has_https` | 1 if HTTPS present | Legitimate sites usually HTTPS |
| `tld_legitimate_prob` | Probability score for TLD legitimacy | `.xyz`, `.tk` = suspicious |
| `url_char_prob` | Character probability score | Random char distributions |
| `char_continuation_rate` | Run-length of consecutive chars | Obfuscation patterns |
| `digit_ratio` | Ratio of digits in URL | `paypa1.com` style attacks |
| `entropy` | Shannon entropy of URL string | High entropy = random/obfuscated |
| `prefix_suffix_hyphen` | Hyphen in domain name | `paypal-secure.com` |
| `special_char_count` | Count of `%`, `=`, `?`, `&` | Query string abuse |

### Category 2 — Webpage Content Features (From HTML source)

Requires fetching the page. Used in offline training, optionally in real-time.

| Feature | Description | Phishing Signal |
|---------|-------------|-----------------|
| `url_title_match_score` | Similarity of URL to page `<title>` | Low match = suspicious |
| `ratio_external_links` | External links / total links | High external ratio |
| `anchor_tag_domains` | Fraction of anchors pointing outside domain | Phishing forms redirect |
| `ssl_final_state` | SSL certificate validity | Invalid SSL = suspicious |
| `favicon_external` | 1 if favicon loaded from external domain | Common phishing trick |
| `num_form_tags` | Count of `<form>` elements | Credential harvesting |
| `has_password_field` | 1 if `<input type=password>` exists | Login form phishing |
| `iframe_count` | Number of iframes | Hidden redirects |
| `meta_refresh_redirect` | 1 if meta refresh redirect present | Auto-redirect trick |
| `script_to_content_ratio` | JS size vs content size | Heavy obfuscated JS |

### Category 3 — Domain/Host Features (From WHOIS/DNS/TLS)

From Zenodo dataset. Useful for domain-level classification.

| Feature | Description | Phishing Signal |
|---------|-------------|-----------------|
| `domain_age_days` | Days since domain registration | Newly registered = suspicious |
| `dns_record_exists` | 1 if valid DNS record exists | Fake domains often lack DNS |
| `whois_registered` | 1 if WHOIS data is present | Hidden WHOIS = suspicious |
| `tls_cert_age_days` | Age of TLS certificate | Very new cert = suspicious |
| `geo_country` | Country of hosting server | Certain regions more phishing |
| `asn_reputation` | ASN known for abuse | Known bad hosting providers |

---

## Data Pipeline

```
Raw Datasets
     │
     ▼
[loader.py] ── Download via ucimlrepo + Zenodo JSON
     │
     ▼
[cleaner.py] ── Drop nulls, deduplicate, fix encoding
     │
     ▼
[url_features.py] ── Extract URL features using tldextract + regex
     │
     ▼
[content_features.py] ── Parse pre-extracted HTML features from UCI
     │
     ▼
[cleaner.py] ── Normalize numeric, encode categoricals
     │
     ▼
[SMOTE] ── Balance class distribution
     │
     ▼
[selector.py] ── RFECV → drop low-importance features
     │
     ▼
[splitter.py] ── Stratified 75/10/15 split
     │
     ├── train.csv
     ├── val.csv
     └── test.csv
```

---

## Models

### Model 1 — Logistic Regression (Baseline)

**Purpose**: Fast sanity-check baseline. Interpretable. Good for understanding linear separability of features.

```python
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(
    C=1.0,
    solver='lbfgs',
    max_iter=1000,
    class_weight='balanced'
)
```

**Expected Accuracy**: ~92–94%

---

### Model 2 — Random Forest

**Purpose**: Ensemble of decision trees. Handles non-linear relationships well. Good for feature importance ranking.

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    min_samples_split=2,
    class_weight='balanced',
    n_jobs=-1,
    random_state=42
)
```

**Expected Accuracy**: ~96–97%

---

### Model 3 — XGBoost (Primary Model)

**Purpose**: Best single model for tabular data. Handles class imbalance via `scale_pos_weight`. Fast inference.

```python
import xgboost as xgb

model = xgb.XGBClassifier(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=1.33,     # ratio of negatives/positives
    use_label_encoder=False,
    eval_metric='logloss',
    random_state=42,
    n_jobs=-1
)
```

**Expected Accuracy**: ~98–99%

---

### Model 4 — LightGBM

**Purpose**: Faster alternative to XGBoost. Better on large datasets. Leaf-wise tree growth.

```python
import lightgbm as lgb

model = lgb.LGBMClassifier(
    n_estimators=500,
    num_leaves=63,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)
```

**Expected Accuracy**: ~98–99%

---

### Model 5 — Deep Neural Network (DNN)

**Purpose**: Captures complex non-linear feature interactions. Used as one layer in the ensemble.

```python
import torch
import torch.nn as nn

class PhishingDNN(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.network(x)
```

**Training**:
- Optimizer: Adam (lr=0.001)
- Loss: BCELoss
- Epochs: 50 with early stopping (patience=5)
- Batch size: 512

**Expected Accuracy**: ~97–98%

---

### Model 6 — Stacked Ensemble (Final Model)

**Architecture**: Base learners feed predictions into a meta-learner.

```
Base Layer:
  ├── XGBoost        → probability score
  ├── LightGBM       → probability score
  ├── Random Forest  → probability score
  └── DNN            → probability score
          │
          ▼
    [Concatenate base predictions + original features]
          │
          ▼
  Meta Layer: Logistic Regression
          │
          ▼
    Final binary prediction (0=legitimate, 1=phishing)
```

```python
from sklearn.ensemble import StackingClassifier
from sklearn.linear_model import LogisticRegression

estimators = [
    ('xgb', xgb_model),
    ('lgbm', lgbm_model),
    ('rf', rf_model),
]

stack = StackingClassifier(
    estimators=estimators,
    final_estimator=LogisticRegression(),
    cv=5,
    passthrough=True      # also passes original features to meta-learner
)
```

**Expected Accuracy**: ~99%+

---

## Training Process

### Step 1 — Load Data

```python
from ucimlrepo import fetch_ucirepo

dataset = fetch_ucirepo(id=967)
X = dataset.data.features
y = dataset.data.targets
```

### Step 2 — Preprocess

```python
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X_scaled, y)
```

### Step 3 — Feature Selection

```python
from sklearn.feature_selection import RFECV
from sklearn.ensemble import RandomForestClassifier

selector = RFECV(
    estimator=RandomForestClassifier(n_estimators=100),
    step=1,
    cv=5,
    scoring='f1'
)
selector.fit(X_resampled, y_resampled)
X_selected = selector.transform(X_resampled)

print(f"Optimal features: {selector.n_features_}")
```

### Step 4 — Train/Val/Test Split

```python
from sklearn.model_selection import train_test_split

X_train, X_temp, y_train, y_temp = train_test_split(
    X_selected, y_resampled,
    test_size=0.25, stratify=y_resampled, random_state=42
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp,
    test_size=0.60, stratify=y_temp, random_state=42
)
# Result: 75% train / 10% val / 15% test
```

### Step 5 — Hyperparameter Tuning with Optuna

```python
import optuna

def objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
    }
    model = xgb.XGBClassifier(**params, random_state=42)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    preds = model.predict(X_val)
    return f1_score(y_val, preds)

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100)
best_params = study.best_params
```

### Step 6 — Train Final Model

```python
import joblib

best_model = xgb.XGBClassifier(**best_params, random_state=42)
best_model.fit(X_train, y_train)

# Save
joblib.dump(best_model, 'models/saved/xgb_best.joblib')
joblib.dump(scaler, 'models/saved/scaler.joblib')
joblib.dump(selector, 'models/saved/selector.joblib')
```

### Step 7 — Evaluate

```python
from sklearn.metrics import (
    classification_report, roc_auc_score,
    confusion_matrix, ConfusionMatrixDisplay
)

y_pred = best_model.predict(X_test)
y_prob = best_model.predict_proba(X_test)[:, 1]

print(classification_report(y_test, y_pred,
      target_names=['Legitimate', 'Phishing']))
print(f"ROC-AUC: {roc_auc_score(y_test, y_prob):.4f}")
```

---

## Evaluation Metrics Explained

| Metric | Formula | Why It Matters |
|--------|---------|----------------|
| **Accuracy** | (TP+TN)/(Total) | Overall correctness |
| **Precision** | TP/(TP+FP) | How many predicted phishing are actually phishing |
| **Recall** | TP/(TP+FN) | How many actual phishing we catch (critical) |
| **F1 Score** | 2×(P×R)/(P+R) | Harmonic mean — balances P and R |
| **ROC-AUC** | Area under ROC curve | Model's discrimination ability |
| **FPR** | FP/(FP+TN) | Legitimate sites wrongly blocked |

> **Priority**: Maximize **Recall** — missing a phishing site is worse than a false alarm.

---

## Model Serialization

Three artifacts are saved per trained model:

```
models/saved/
├── xgb_best.joblib        # Trained XGBoost model
├── scaler.joblib          # StandardScaler fitted on train data
└── selector.joblib        # RFECV feature selector
```

Inference pipeline at prediction time:

```python
url_features → scaler.transform() → selector.transform() → model.predict_proba()
```

---

## Class Labels

| Label | Value | Meaning |
|-------|-------|---------|
| 0 | Legitimate | Safe website |
| 1 | Phishing | Malicious website |

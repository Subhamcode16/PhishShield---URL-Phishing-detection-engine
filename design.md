# Phishing Website Detection — System Design

## Architecture Overview

```
                        ┌─────────────────────────────────┐
                        │         CLIENT / USER            │
                        │  (Browser Extension / App / API) │
                        └────────────────┬────────────────┘
                                         │ HTTP POST /predict
                                         ▼
                        ┌─────────────────────────────────┐
                        │         FastAPI Server           │
                        │  ┌─────────────────────────┐    │
                        │  │  Auth Middleware          │    │
                        │  │  Rate Limiter             │    │
                        │  │  Request Validator        │    │
                        │  └────────────┬────────────┘    │
                        │               │                  │
                        │  ┌────────────▼────────────┐    │
                        │  │   Feature Extractor      │    │
                        │  │   (URL → Feature Vector) │    │
                        │  └────────────┬────────────┘    │
                        │               │                  │
                        │  ┌────────────▼────────────┐    │
                        │  │   Inference Engine       │    │
                        │  │   scaler → selector      │    │
                        │  │   → model.predict_proba  │    │
                        │  └────────────┬────────────┘    │
                        │               │                  │
                        │  ┌────────────▼────────────┐    │
                        │  │   Response Builder       │    │
                        │  │   + Confidence Score     │    │
                        │  └────────────┬────────────┘    │
                        └───────────────┼─────────────────┘
                                        │
                   ┌────────────────────┼───────────────────┐
                   ▼                    ▼                    ▼
          ┌──────────────┐    ┌──────────────────┐  ┌──────────────┐
          │   MongoDB    │    │  JSON Response   │  │  Log File    │
          │  predictions │    │  to Client       │  │  (audit)     │
          │  collection  │    │                  │  │              │
          └──────────────┘    └──────────────────┘  └──────────────┘
```

---

## Setup Guide

### Prerequisites

- Python 3.10+
- Docker + Docker Compose
- MongoDB (local or Atlas)
- 4GB+ RAM recommended for training

---

### 1. Clone & Create Environment

```bash
git clone https://github.com/yourname/phishing-detection.git
cd phishing-detection

python -m venv venv
source venv/bin/activate          # Linux/Mac
# OR
venv\Scripts\activate             # Windows

pip install -r requirements.txt
```

---

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
MONGO_URI=mongodb://localhost:27017
DB_NAME=phishing_detection
API_KEY=your_secret_key_here
MODEL_PATH=models/saved/best_model.joblib
LOG_LEVEL=INFO
```

---

### 3. Download Datasets

```bash
python src/data/loader.py
```

`loader.py` does the following automatically:

```python
# UCI PhiUSIIL (id=967)
from ucimlrepo import fetch_ucirepo
dataset = fetch_ucirepo(id=967)
X = dataset.data.features
y = dataset.data.targets
df = pd.concat([X, y], axis=1)
df.to_csv('data/raw/phiusiil_uci.csv', index=False)

# UCI Classic (id=327)
classic = fetch_ucirepo(id=327)
classic_df = pd.concat([classic.data.features, classic.data.targets], axis=1)
classic_df.to_csv('data/raw/uci_classic.csv', index=False)

# Zenodo (manual download — link below)
# https://zenodo.org/records/8364668
# Place benign_2307.json and phishing_2307.json in data/raw/
```

---

### 4. Preprocess Data

```bash
python src/data/cleaner.py
```

This will:
- Merge all datasets on common features
- Drop nulls and duplicate rows
- Normalize numeric columns
- Apply SMOTE for class balancing
- Save to `data/processed/`

---

### 5. Train the Model

```bash
python src/training/trainer.py --model xgboost --tune True
```

**Flags:**

| Flag | Options | Default |
|------|---------|---------|
| `--model` | `logistic`, `rf`, `xgboost`, `lgbm`, `dnn`, `ensemble` | `xgboost` |
| `--tune` | `True` / `False` | `False` |
| `--trials` | integer | `100` |
| `--save` | `True` / `False` | `True` |

**What happens during training:**

```
1. Load data/processed/train.csv + val.csv
2. Fit StandardScaler on train set
3. Run RFECV feature selection
4. If --tune True → run Optuna for N trials
5. Train final model with best params
6. Evaluate on val set → print metrics
7. Save model + scaler + selector to models/saved/
```

---

### 6. Evaluate on Test Set

```bash
python src/training/evaluator.py --model models/saved/xgb_best.joblib
```

Outputs:
- Classification report (precision, recall, F1 per class)
- ROC-AUC score
- Confusion matrix plot saved to `models/reports/`
- Feature importance chart

---

### 7. Start the API

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

API will be live at: `http://localhost:8000`

Docs UI: `http://localhost:8000/docs`

---

### 8. Run with Docker

```bash
docker-compose up --build
```

`docker-compose.yml`:

```yaml
version: "3.9"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGO_URI=mongodb://mongo:27017
      - DB_NAME=phishing_detection
      - MODEL_PATH=models/saved/best_model.joblib
    volumes:
      - ./models:/app/models
    depends_on:
      - mongo

  mongo:
    image: mongo:6
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

`Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## API Design

### POST `/predict`

Predict a single URL.

**Request:**
```json
{
  "url": "http://paypa1-secure.xyz/login?ref=account"
}
```

**Response:**
```json
{
  "url": "http://paypa1-secure.xyz/login?ref=account",
  "prediction": "phishing",
  "label": 1,
  "confidence": 0.9847,
  "risk_score": "HIGH",
  "features_used": 24,
  "model_version": "xgb_v1.2",
  "timestamp": "2026-05-10T14:32:00Z"
}
```

---

### POST `/batch`

Predict multiple URLs in one call.

**Request:**
```json
{
  "urls": [
    "https://google.com",
    "http://paypa1-secure.xyz/login",
    "https://github.com"
  ]
}
```

**Response:**
```json
{
  "results": [
    { "url": "https://google.com", "prediction": "legitimate", "confidence": 0.9991 },
    { "url": "http://paypa1-secure.xyz/login", "prediction": "phishing", "confidence": 0.9847 },
    { "url": "https://github.com", "prediction": "legitimate", "confidence": 0.9978 }
  ],
  "total": 3,
  "phishing_count": 1,
  "timestamp": "2026-05-10T14:32:00Z"
}
```

---

### GET `/health`

```json
{
  "status": "ok",
  "model_loaded": true,
  "model_version": "xgb_v1.2",
  "uptime_seconds": 3842
}
```

---

## FastAPI Code Skeleton

### `src/api/schema.py`

```python
from pydantic import BaseModel, HttpUrl
from typing import List

class PredictRequest(BaseModel):
    url: str

class PredictResponse(BaseModel):
    url: str
    prediction: str
    label: int
    confidence: float
    risk_score: str
    features_used: int
    model_version: str
    timestamp: str

class BatchRequest(BaseModel):
    urls: List[str]
```

### `src/api/main.py`

```python
from fastapi import FastAPI, Depends, HTTPException, Header
from contextlib import asynccontextmanager
import joblib
import os

from .schema import PredictRequest, PredictResponse, BatchRequest
from ..features.url_features import extract_url_features

model = None
scaler = None
selector = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, scaler, selector
    model   = joblib.load(os.getenv("MODEL_PATH"))
    scaler  = joblib.load("models/saved/scaler.joblib")
    selector = joblib.load("models/saved/selector.joblib")
    yield

app = FastAPI(title="Phishing Detection API", version="1.0.0", lifespan=lifespan)

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API Key")

@app.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest, _=Depends(verify_api_key)):
    features = extract_url_features(req.url)
    X = scaler.transform([features])
    X = selector.transform(X)
    prob = model.predict_proba(X)[0][1]
    label = int(prob >= 0.5)
    return {
        "url": req.url,
        "prediction": "phishing" if label == 1 else "legitimate",
        "label": label,
        "confidence": round(float(prob if label == 1 else 1 - prob), 4),
        "risk_score": "HIGH" if prob > 0.8 else "MEDIUM" if prob > 0.5 else "LOW",
        "features_used": X.shape[1],
        "model_version": "xgb_v1.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None}
```

---

## MongoDB Schema

**Collection: `predictions`**

```json
{
  "_id": "ObjectId",
  "url": "http://paypa1-secure.xyz/login",
  "prediction": "phishing",
  "label": 1,
  "confidence": 0.9847,
  "risk_score": "HIGH",
  "features": { ... },
  "model_version": "xgb_v1.0",
  "ip_address": "1.2.3.4",
  "created_at": "2026-05-10T14:32:00Z"
}
```

**Collection: `model_runs`**

```json
{
  "_id": "ObjectId",
  "model_name": "xgboost",
  "version": "v1.2",
  "accuracy": 0.9912,
  "f1": 0.9908,
  "roc_auc": 0.9981,
  "train_size": 176241,
  "test_size": 35248,
  "features_selected": 24,
  "trained_at": "2026-05-10T10:00:00Z"
}
```

---

## Risk Score Logic

```python
def get_risk_score(prob: float) -> str:
    if prob >= 0.85:
        return "CRITICAL"
    elif prob >= 0.65:
        return "HIGH"
    elif prob >= 0.45:
        return "MEDIUM"
    else:
        return "LOW"
```

---

## URL Feature Extraction (Core Logic)

```python
# src/features/url_features.py
import re
import math
import tldextract
from urllib.parse import urlparse

def extract_url_features(url: str) -> list:
    parsed = urlparse(url)
    ext = tldextract.extract(url)

    domain = ext.domain + '.' + ext.suffix
    full_url = url

    def shannon_entropy(s):
        prob = [float(s.count(c)) / len(s) for c in set(s)]
        return -sum(p * math.log2(p) for p in prob)

    features = [
        len(full_url),                                       # url_length
        len(ext.domain),                                     # domain_length
        full_url.count('.'),                                 # num_dots
        full_url.count('-'),                                 # num_hyphens
        full_url.count('@'),                                 # num_at_symbols
        full_url.count('/'),                                 # num_slashes
        len(ext.subdomain.split('.')) if ext.subdomain else 0,  # num_subdomains
        1 if re.match(r'\d+\.\d+\.\d+\.\d+', ext.domain) else 0, # has_ip
        1 if parsed.scheme == 'https' else 0,               # has_https
        full_url.count('%'),                                 # percent_encoding
        sum(c.isdigit() for c in full_url) / len(full_url), # digit_ratio
        shannon_entropy(full_url),                           # entropy
        1 if '-' in ext.domain else 0,                      # prefix_suffix_hyphen
        len(re.findall(r'[%=?&]', full_url)),               # special_char_count
    ]
    return features
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Test specific
pytest tests/test_api.py -v
pytest tests/test_features.py -v
pytest tests/test_model.py -v
```

**Sample API test:**

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_predict_phishing():
    response = client.post(
        "/predict",
        json={"url": "http://paypa1-secure.xyz/login"},
        headers={"x-api-key": "test_key"}
    )
    assert response.status_code == 200
    assert response.json()["prediction"] == "phishing"

def test_predict_legitimate():
    response = client.post(
        "/predict",
        json={"url": "https://github.com"},
        headers={"x-api-key": "test_key"}
    )
    assert response.status_code == 200
    assert response.json()["prediction"] == "legitimate"
```

---

## Future Improvements

- **Real-time retraining**: Ingest new phishing URLs from PhishTank API daily, retrain weekly
- **Browser extension**: Chrome/Firefox extension that calls `/predict` on every page load
- **Adversarial robustness**: Add adversarial URL examples to training set to prevent evasion
- **LLM-assisted feature extraction**: Use Claude Haiku to extract semantic features from page content
- **Feedback loop**: Allow users to flag incorrect predictions → feed back to training pipeline

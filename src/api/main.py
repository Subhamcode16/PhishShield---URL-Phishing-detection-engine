from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import os
import sys
import uvicorn
import re
import tldextract

# Ensure we can load our local modules
sys.path.append(os.getcwd())
from src.features.url_features import extract_url_features

app = FastAPI(title="PhishShield Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = "models/saved/best_model.joblib"
SCALER_PATH = "models/saved/scaler.joblib"

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

class URLRequest(BaseModel):
    url: str

@app.post("/predict")
async def predict(request: URLRequest):
    url = request.url.strip().lower()
    print(f"Analyzing URL: {url}")
    
    features = extract_url_features(url)
    X = scaler.transform([list(features.values())])
    
    # 0. WHITELIST (Known Safe Domains)
    whitelist = ['google.com', 'facebook.com', 'apple.com', 'microsoft.com', 'amazon.com', 'github.com', 'wikipedia.org', 'youtube.com']
    actual_full_domain = tldextract.extract(url).domain + "." + tldextract.extract(url).suffix
    
    if actual_full_domain in whitelist:
        return {
            "prediction": "Legitimate",
            "is_phishing": False,
            "confidence": 1.0,
            "risk_score": "LOW",
            "features_used": len(extract_url_features(url)),
            "reason": "Whitelisted Domain"
        }

    # 1. ML Prediction
    prediction = int(model.predict(X)[0])
    
    # 2. HEURISTIC OVERRIDE (Absolute Brand Protection)
    domain_only = tldextract.extract(url).domain
    
    # Powerful check for brand tricks
    brand_tricks = [
        (r'am[a4]z[o0]n', "Amazon Impersonation"),
        (r'p[a4]yp[a4][l1!|i]', "PayPal Impersonation"),
        (r'f[a4]c[e3]b[o0][o0]k', "Facebook Impersonation"),
        (r'g[o0][o0]gl[e3]', "Google Impersonation"),
        (r'm[i1]cr[o0]s[o0]ft', "Microsoft Impersonation"),
        (r'st[e3]am', "Steam Impersonation"),
        (r'n[e3]tfl[i1]x', "Netflix Impersonation")
    ]
    
    found_trick = False
    reason = "ML Analysis"
    
    for pattern, name in brand_tricks:
        # NEW: Search the WHOLE URL, not just the domain
        if re.search(pattern, url):
            # Special case: don't flag the ACTUAL brands
            official_domains = ['amazon', 'paypal', 'facebook', 'google', 'microsoft']
            actual_domain = tldextract.extract(url).domain.lower()
            if actual_domain not in official_domains:
                prediction = 1
                found_trick = True
                reason = name
                break
    
    confidence = 0.999 if found_trick else round(float(model.predict_proba(X)[0][prediction]), 4)

    return {
        "prediction": "Phishing" if prediction == 1 else "Legitimate",
        "is_phishing": bool(prediction),
        "confidence": confidence,
        "risk_score": "CRITICAL" if found_trick else ("HIGH" if prediction == 1 else "LOW"),
        "features_used": len(features),
        "reason": reason
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)

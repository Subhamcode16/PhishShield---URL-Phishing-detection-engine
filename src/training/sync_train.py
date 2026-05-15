import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
import sys

# Ensure we can load our local modules
sys.path.append(os.getcwd())
from src.features.url_features import extract_url_features

def sync_and_train():
    print("Loading Dataset (PhiUSIIL)...")
    if not os.path.exists('data/raw/PhiUSIIL_Phishing_URL_Dataset.csv'):
        print("Error: Dataset not found.")
        return
        
    df = pd.read_csv('data/raw/PhiUSIIL_Phishing_URL_Dataset.csv').sample(30000, random_state=42)
    
    print("Extracting 21 Features (Homoglyph Aware)...")
    X_list = []
    y_list = []
    
    for url, label in zip(df['URL'], df['label']):
        f = extract_url_features(url)
        if f:
            X_list.append(list(f.values()))
            y_list.append(label)
            
    X = np.array(X_list)
    y = np.array(y_list)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Balancing Features (Scaler)...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    print("Training XGBoost (High-Precision)...")
    model = XGBClassifier(eval_metric='logloss', n_estimators=100)
    model.fit(X_train_scaled, y_train)
    
    print("Saving Synced Assets...")
    if not os.path.exists('models/saved'):
        os.makedirs('models/saved')
        
    joblib.dump(model, 'models/saved/best_model.joblib')
    joblib.dump(scaler, 'models/saved/scaler.joblib')
    
    acc = model.score(scaler.transform(X_test), y_test)
    print(f"SUCCESS: New Accuracy: {acc*100:.2f}%")

if __name__ == "__main__":
    sync_and_train()

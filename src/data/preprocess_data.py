import pandas as pd
import numpy as np
import os
import sys

# Add src to path so we can import url_features
sys.path.append(os.getcwd())
from src.features.url_features import extract_url_features
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

def preprocess():
    print("Loading datasets...")
    raw_path = 'data/raw/PhiUSIIL_Phishing_URL_Dataset.csv'
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} not found.")
        return
    
    df_phi = pd.read_csv(raw_path)
    
    print(f"Extracting features from {len(df_phi)} URLs...")
    
    # Use a large sample for robust training (50k samples)
    sample_size = min(50000, len(df_phi))
    sample_df = df_phi.sample(n=sample_size, random_state=42)
    
    features_list = []
    labels = []
    
    # Process in batches for progress reporting
    total = len(sample_df)
    for i, (_, row) in enumerate(sample_df.iterrows()):
        f = extract_url_features(row['URL'])
        if f:
            features_list.append(list(f.values()))
            labels.append(row['label'])
        if (i + 1) % 10000 == 0:
            print(f"  Processed {i+1}/{total} URLs...")
            
    # Create feature names
    dummy_features = extract_url_features("http://test.com")
    feature_names = list(dummy_features.keys())
    X = pd.DataFrame(features_list, columns=feature_names)
    y = np.array(labels)
    
    print(f"Extracted {X.shape[1]} features for {X.shape[0]} samples.")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Save the scaler for inference
    os.makedirs('models/saved', exist_ok=True)
    joblib.dump(scaler, 'models/saved/scaler.joblib')
    print("Saved Scaler to models/saved/scaler.joblib")
    
    return X_train_scaled, X_test_scaled, y_train, y_test, feature_names

if __name__ == "__main__":
    X_train, X_test, y_train, y_test, feature_names = preprocess()
    # Save processed data for the training script
    np.savez('data/processed_data.npz', X_train=X_train, X_test=X_test, y_train=y_train, y_test=y_test)
    print("✅ Preprocessing complete. Data saved to data/processed_data.npz")

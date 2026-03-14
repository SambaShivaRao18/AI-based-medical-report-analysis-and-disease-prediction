# modules/symptom_checker_ml/train_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
import os

print("📊 Training Symptom Prediction Model...")

# Load the data
data = pd.read_csv('data/symptom_disease_data.csv')

# Separate features and target
X = data.drop('Disease', axis=1)
y = data['Disease']

# Encode disease labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Train model
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    class_weight='balanced'
)

model.fit(X, y_encoded)

# Save model and encoder
joblib.dump(model, 'models/symptom_model.pkl')
joblib.dump(label_encoder, 'models/label_encoder.pkl')
joblib.dump(X.columns.tolist(), 'models/feature_names.pkl')

print(f"✅ Model trained on {len(X)} samples with {len(X.columns)} symptoms")
print(f"📁 Model saved to models/symptom_model.pkl")
print(f"📁 Label encoder saved to models/label_encoder.pkl")
print(f"📁 Feature names saved to models/feature_names.pkl")
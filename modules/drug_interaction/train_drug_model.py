# train_drug_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import json

print("💊 Training Enhanced Drug Interaction Model...")

# Load the data
df = pd.read_csv('data/drug_interactions.csv')

# Create feature engineering
all_drugs = sorted(list(set(df['Drug1'].unique()) | set(df['Drug2'].unique())))
print(f"📊 Total unique drugs: {len(all_drugs)}")

# Create drug pairs and encode
drug_pairs = []
severities = []
interaction_types = []
descriptions = []
mechanisms = []
recommendations = []
spacing_effectiveness = []
alternatives = []
monitoring_advice = []

for _, row in df.iterrows():
    drug_pair = tuple(sorted([row['Drug1'], row['Drug2']]))
    drug_pairs.append(drug_pair)
    severities.append(row['Severity'])
    interaction_types.append(row['InteractionType'])
    descriptions.append(row['Description'])
    mechanisms.append(row['Mechanism'])
    recommendations.append(row['Recommendation'])
    spacing_effectiveness.append(row['SpacingEffectiveness'])
    alternatives.append(row['Alternatives'])
    monitoring_advice.append(row['MonitoringAdvice'])

# Create binary feature vectors
drug_to_idx = {drug: i for i, drug in enumerate(all_drugs)}
n_drugs = len(all_drugs)

X = []
for pair in drug_pairs:
    vec = [0] * n_drugs
    vec[drug_to_idx[pair[0]]] = 1
    vec[drug_to_idx[pair[1]]] = 1
    X.append(vec)

X = np.array(X)

# Encode severity
severity_encoder = LabelEncoder()
y = severity_encoder.fit_transform(severities)

# Train model
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    random_state=42,
    class_weight='balanced'
)

model.fit(X, y)
print(f"✅ Model trained on {len(X)} drug pairs")

# Save everything
joblib.dump(model, 'models/drug_model.pkl')
joblib.dump(severity_encoder, 'models/severity_encoder.pkl')
joblib.dump(all_drugs, 'models/all_drugs.pkl')

# Save the enhanced interaction database
interaction_db = {}
for i, pair in enumerate(drug_pairs):
    key = f"{pair[0]}-{pair[1]}"
    interaction_db[key] = {
        'severity': severities[i],
        'interaction_type': interaction_types[i],
        'description': descriptions[i],
        'mechanism': mechanisms[i],
        'recommendation': recommendations[i],
        'spacing_effectiveness': spacing_effectiveness[i],
        'alternatives': alternatives[i],
        'monitoring_advice': monitoring_advice[i]
    }

with open('models/interaction_db.json', 'w') as f:
    json.dump(interaction_db, f, indent=2)

print(f"📁 Models saved to models/ directory")
print(f"📊 Severity classes: {severity_encoder.classes_.tolist()}")
print(f"📊 Total interactions: {len(interaction_db)}")
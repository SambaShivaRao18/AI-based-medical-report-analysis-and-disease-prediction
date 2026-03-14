# modules/symptom_checker_ml/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import pandas as pd
import os
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
import json
import re

app = Flask(__name__)
CORS(app)

# Load ML model
print("🔄 Loading ML model...")
try:
    model = joblib.load('models/symptom_model.pkl')
    label_encoder = joblib.load('models/label_encoder.pkl')
    feature_names = joblib.load('models/feature_names.pkl')
    print(f"✅ ML Model loaded with {len(feature_names)} symptoms and {len(label_encoder.classes_)} diseases")
    ml_available = True
except Exception as e:
    print(f"⚠️ ML Model not found: {e}")
    ml_available = False

# Initialize LLM for fallback
print("🧠 Initializing Groq LLM for fallback...")
try:
    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile",
        temperature=0.2,
        max_tokens=1500
    )
    llm_available = True
    print("✅ LLM fallback ready")
except Exception as e:
    print(f"⚠️ LLM not available: {e}")
    llm_available = False

# Disease information database (for ML model results)
disease_info = {
    'Common Cold': {
        'description': 'A viral infection of the upper respiratory tract. Usually harmless and self-limiting.',
        'recommendations': [
            'Rest and stay hydrated',
            'Over-the-counter cold medications for symptom relief',
            'Honey and warm tea for sore throat',
            'Consult doctor if symptoms persist beyond 10 days'
        ]
    },
    'Flu': {
        'description': 'Influenza is a contagious respiratory illness caused by influenza viruses.',
        'recommendations': [
            'Rest and isolate to prevent spread',
            'Drink plenty of fluids',
            'Take acetaminophen or ibuprofen for fever',
            'Antiviral medications if caught early',
            'Seek medical help if breathing difficulties occur'
        ]
    },
    'COVID-19': {
        'description': 'A contagious respiratory illness caused by SARS-CoV-2 virus.',
        'recommendations': [
            'Get tested immediately',
            'Isolate from others',
            'Monitor oxygen levels',
            'Seek emergency care if breathing difficulty',
            'Follow CDC guidelines for quarantine'
        ]
    },
    'Allergies': {
        'description': 'Immune system reaction to normally harmless substances like pollen, dust, or pet dander.',
        'recommendations': [
            'Avoid known allergens',
            'Take antihistamines',
            'Use nasal sprays as recommended',
            'Consider allergy testing',
            'Keep windows closed during high pollen'
        ]
    },
    'Migraine': {
        'description': 'A neurological condition causing severe, recurring headaches often with other symptoms.',
        'recommendations': [
            'Rest in dark, quiet room',
            'Apply cold compress to forehead',
            'Stay hydrated',
            'Avoid known triggers',
            'Consult neurologist for recurring episodes'
        ]
    },
    'Gastroenteritis': {
        'description': 'Inflammation of the stomach and intestines, often called stomach flu.',
        'recommendations': [
            'Stay hydrated with clear fluids',
            'Follow BRAT diet (bananas, rice, applesauce, toast)',
            'Rest digestive system',
            'Avoid dairy and fatty foods',
            'Seek help if severe dehydration'
        ]
    },
    'Pneumonia': {
        'description': 'Infection that inflames air sacs in one or both lungs, which may fill with fluid.',
        'recommendations': [
            'Immediate medical attention needed',
            'Take prescribed antibiotics',
            'Rest and stay hydrated',
            'Use fever reducers',
            'Follow up with doctor'
        ]
    },
    'Bronchitis': {
        'description': 'Inflammation of the bronchial tubes, often after a cold or flu.',
        'recommendations': [
            'Rest and drink fluids',
            'Use humidifier',
            'Avoid smoke and irritants',
            'Cough drops for throat',
            'See doctor if fever persists'
        ]
    },
    'Strep Throat': {
        'description': 'Bacterial infection causing painful, scratchy throat.',
        'recommendations': [
            'Antibiotics required - see doctor',
            'Gargle warm salt water',
            'Drink warm tea with honey',
            'Rest voice',
            'Replace toothbrush after antibiotics'
        ]
    },
    'Sinusitis': {
        'description': 'Inflammation or swelling of the tissue lining the sinuses.',
        'recommendations': [
            'Nasal irrigation with saline',
            'Use warm compresses',
            'Inhale steam',
            'Stay hydrated',
            'See ENT if chronic'
        ]
    },
    'Asthma': {
        'description': 'Condition where airways narrow and swell, producing extra mucus.',
        'recommendations': [
            'Use prescribed inhalers',
            'Avoid triggers',
            'Monitor breathing',
            'Create asthma action plan',
            'Seek emergency if rescue inhaler not helping'
        ]
    },
    'Food Poisoning': {
        'description': 'Illness caused by eating contaminated food.',
        'recommendations': [
            'Stay hydrated with electrolytes',
            'Rest stomach - avoid food initially',
            'Gradually introduce bland foods',
            'See doctor if severe or bloody diarrhea',
            'Report suspected food source'
        ]
    },
    'Mononucleosis': {
        'description': 'Viral infection causing fatigue, fever, and swollen lymph nodes.',
        'recommendations': [
            'Rest - can last weeks',
            'Stay hydrated',
            'Avoid contact sports (spleen risk)',
            'Take acetaminophen for pain',
            'See doctor for confirmation'
        ]
    },
    'UTI': {
        'description': 'Infection in any part of the urinary system.',
        'recommendations': [
            'Drink plenty of water',
            'Urinate frequently',
            'See doctor for antibiotics',
            'Cranberry juice may help',
            'Avoid irritants like caffeine'
        ]
    },
    'Influenza': {
        'description': 'Severe viral respiratory infection with sudden onset.',
        'recommendations': [
            'Rest and fluids',
            'Take antivirals if prescribed',
            'Use fever reducers',
            'Isolate from others',
            'Watch for breathing difficulties'
        ]
    }
}

def get_llm_prediction(symptoms_list):
    """Get predictions from LLM for any symptoms"""
    symptoms_text = ", ".join(symptoms_list)
    
    prompt = PromptTemplate(
        template="""You are a medical diagnosis AI. Based on the following symptoms, provide the top 5 most likely conditions.

Symptoms: {symptoms}

Return ONLY a valid JSON array with NO additional text. Each item should have:
- name: condition name
- probability: number between 0-100
- description: brief description
- recommendations: array of 3-4 recommendations

Example format:
[
  {{
    "name": "Condition Name",
    "probability": 85,
    "description": "Brief description of the condition",
    "recommendations": ["recommendation1", "recommendation2", "recommendation3"]
  }}
]

JSON response:""",
        input_variables=["symptoms"]
    )
    
    try:
        response = llm.invoke(prompt.format(symptoms=symptoms_text))
        
        # Extract JSON from response
        response_text = response.content
        # Find JSON array
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            predictions = json.loads(json_str)
            return predictions[:5]  # Return top 5
        else:
            # Fallback format
            return [{
                'name': 'Multiple conditions possible',
                'probability': 50,
                'description': f'Based on symptoms: {symptoms_text}',
                'recommendations': ['Consult healthcare provider', 'Monitor symptoms', 'Seek medical attention if worsens']
            }]
    except Exception as e:
        print(f"❌ LLM error: {e}")
        return None

@app.route('/api/symptoms/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        symptoms = data.get('symptoms', [])
        
        if not symptoms or len(symptoms) < 2:
            return jsonify({
                'success': False,
                'error': 'Please select at least 2 symptoms'
            }), 400
        
        print(f"\n🔍 Predicting for symptoms: {symptoms}")
        
        # Try ML model first
        ml_predictions = None
        unknown_symptoms = []
        
        if ml_available:
            try:
                # Create feature vector
                feature_vector = np.zeros(len(feature_names))
                
                # Map symptoms to features
                for symptom in symptoms:
                    if symptom in feature_names:
                        idx = feature_names.index(symptom)
                        feature_vector[idx] = 1
                    else:
                        unknown_symptoms.append(symptom)
                
                # If we have at least 2 known symptoms, use ML
                known_count = len(symptoms) - len(unknown_symptoms)
                if known_count >= 2:
                    probabilities = model.predict_proba([feature_vector])[0]
                    top_indices = np.argsort(probabilities)[-5:][::-1]
                    
                    ml_predictions = []
                    for idx in top_indices:
                        if probabilities[idx] > 0.05:
                            disease_name = label_encoder.inverse_transform([idx])[0]
                            probability = probabilities[idx] * 100
                            
                            info = disease_info.get(disease_name, {
                                'description': 'No description available',
                                'recommendations': ['Consult healthcare provider']
                            })
                            
                            ml_predictions.append({
                                'name': disease_name,
                                'probability': round(probability, 1),
                                'description': info['description'],
                                'recommendations': info['recommendations']
                            })
                    
                    print(f"✅ ML model generated {len(ml_predictions)} predictions")
            except Exception as e:
                print(f"⚠️ ML prediction failed: {e}")
                ml_predictions = None
        
        # If ML didn't work well or had unknown symptoms, use LLM
        final_predictions = None
        used_fallback = False
        
        if ml_predictions and len(ml_predictions) >= 2 and len(unknown_symptoms) == 0:
            # ML worked perfectly
            final_predictions = ml_predictions
            print("✅ Using ML model predictions")
        elif llm_available:
            # Use LLM fallback
            print("🔄 Using LLM fallback for unknown symptoms")
            llm_predictions = get_llm_prediction(symptoms)
            if llm_predictions:
                final_predictions = llm_predictions
                used_fallback = True
                print("✅ Using LLM predictions")
        
        if not final_predictions:
            return jsonify({
                'success': False,
                'error': 'Could not generate predictions'
            }), 500
        
        return jsonify({
            'success': True,
            'predictions': final_predictions,
            'used_fallback': used_fallback,
            'unknown_symptoms': unknown_symptoms if unknown_symptoms else None
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/symptoms/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'ml_available': ml_available,
        'llm_available': llm_available,
        'symptoms_count': len(feature_names) if ml_available else 0,
        'diseases_count': len(label_encoder.classes_) if ml_available else 0
    })

if __name__ == '__main__':
    print("🚀 Symptom Checker starting on port 5003...")
    app.run(host='0.0.0.0', port=5003, debug=True)
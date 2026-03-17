# modules/drug_interaction/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import pandas as pd
import json
import os
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
import re
from itertools import combinations
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load ML model
print("💊 Loading Drug Interaction ML model...")
try:
    model = joblib.load('models/drug_model.pkl')
    severity_encoder = joblib.load('models/severity_encoder.pkl')
    all_drugs = joblib.load('models/all_drugs.pkl')
    with open('models/interaction_db.json', 'r') as f:
        interaction_db = json.load(f)
    
    drug_to_idx = {drug: i for i, drug in enumerate(all_drugs)}
    print(f"✅ ML Model loaded with {len(all_drugs)} drugs and {len(interaction_db)} known interactions")
    ml_available = True
except Exception as e:
    print(f"⚠️ ML Model not found: {e}")
    ml_available = False
    interaction_db = {}

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

def get_drug_pair_key(drug1, drug2):
    """Create a standardized key for drug pair"""
    drugs = sorted([drug1.strip().title(), drug2.strip().title()])
    return f"{drugs[0]}-{drugs[1]}"

def parse_time(time_str):
    """Parse time string like '8:00AM', '8:00 AM', '8:00am', '08:00' etc to hours"""
    try:
        if not time_str or time_str.strip() == '':
            return None
        
        # Clean the time string
        time_str = time_str.strip()
        print(f"⏰ Parsing time: '{time_str}'")
        
        # Handle different formats
        time_str_upper = time_str.upper()
        
        # Check if it contains AM or PM
        if 'AM' in time_str_upper or 'PM' in time_str_upper:
            # Remove any spaces
            clean_time = time_str_upper.replace(' ', '')
            
            # Extract the part before AM/PM
            if 'AM' in clean_time:
                time_part = clean_time.replace('AM', '')
                meridiem = 'AM'
            else:  # PM
                time_part = clean_time.replace('PM', '')
                meridiem = 'PM'
            
            # Parse hour and minute
            if ':' in time_part:
                hour, minute = map(int, time_part.split(':'))
            else:
                hour = int(time_part)
                minute = 0
            
            # Validate hour
            if hour < 1 or hour > 12:
                print(f"⚠️ Invalid hour: {hour}")
                return None
            
            # Create time string in the expected format
            formatted_time = f"{hour}:{minute:02d} {meridiem}"
            print(f"✅ Formatted time: '{formatted_time}'")
            
            # Parse with the correct format
            time_obj = datetime.strptime(formatted_time, "%I:%M %p")
            return time_obj
        else:
            # Try 24-hour format
            if ':' in time_str:
                return datetime.strptime(time_str, "%H:%M")
            else:
                return datetime.strptime(time_str, "%H%M")
            
    except Exception as e:
        print(f"⚠️ Time parsing error for '{time_str}': {e}")
        return None

def calculate_hours_gap(timing1, timing2):
    """Calculate hours difference between two times"""
    try:
        print(f"⏰ Calculating gap between '{timing1}' and '{timing2}'")
        
        time1_obj = parse_time(timing1)
        time2_obj = parse_time(timing2)
        
        if not time1_obj or not time2_obj:
            print(f"⚠️ Could not parse times")
            return None
        
        # Calculate difference in hours
        diff_seconds = abs((time2_obj - time1_obj).total_seconds())
        diff_hours = diff_seconds / 3600
        
        # If difference is more than 12 hours, it might be overnight
        # In that case, take the smaller gap
        if diff_hours > 12:
            diff_hours = 24 - diff_hours
        
        diff_hours = round(diff_hours, 1)
        print(f"✅ Gap calculated: {diff_hours} hours")
        return diff_hours
        
    except Exception as e:
        print(f"⚠️ Hours gap calculation error: {e}")
        return None

def analyze_timing_and_update_recommendation(interaction, timing1, timing2):
    """
    Analyze timing gap and provide ACCURATE recommendations based on medical facts
    """
    if not timing1 or not timing2:
        return interaction
    
    try:
        # Calculate hours gap
        diff_hours = calculate_hours_gap(timing1, timing2)
        
        if diff_hours is None:
            return interaction
        
        # Get interaction details
        severity = interaction.get('severity', 'safe')
        spacing_effectiveness = interaction.get('spacing_effectiveness', 'unknown')
        
        # Store gap info
        interaction['hours_gap'] = diff_hours
        
        # Generate ACCURATE recommendation based on medical facts
        if severity == 'danger':
            if spacing_effectiveness == 'high':
                # Some dangerous interactions CAN be managed with spacing
                if diff_hours >= 8:
                    interaction['recommendation'] = (
                        f"⚠️ DANGEROUS INTERACTION: {interaction['med1']} + {interaction['med2']}\n\n"
                        f"• Your {diff_hours}-hour gap reduces but does NOT eliminate risk.\n"
                        f"• These medications affect your body for 24+ hours.\n"
                        f"• Watch for: {interaction.get('monitoring_advice', 'bleeding signs')}\n\n"
                        f"✅ Safer alternatives: {interaction.get('alternatives', 'Consult your doctor')}"
                    )
                else:
                    interaction['recommendation'] = (
                        f"⚠️ DANGEROUS INTERACTION - INSUFFICIENT SPACING\n\n"
                        f"• Only {diff_hours} hours between doses (need 8+ hours).\n"
                        f"• Even with spacing, this combination is risky.\n"
                        f"• {interaction.get('recommendation', 'Avoid this combination')}\n\n"
                        f"✅ Alternatives: {interaction.get('alternatives', 'Consult your doctor')}"
                    )
            else:
                # Dangerous interactions where spacing doesn't help
                interaction['recommendation'] = (
                    f"🚨 CRITICAL: DANGEROUS INTERACTION\n\n"
                    f"• {interaction['description']}\n"
                    f"• {interaction['mechanism']}\n"
                    f"• ⚠️ SPACING DOSES DOES NOT MAKE THIS SAFE ⚠️\n\n"
                    f"✅ RECOMMENDATION: {interaction.get('recommendation', 'Avoid this combination')}\n"
                    f"✅ SAFER OPTIONS: {interaction.get('alternatives', 'Consult your doctor')}\n"
                    f"✅ MONITOR FOR: {interaction.get('monitoring_advice', 'Seek medical help if symptoms occur')}"
                )
                
        elif severity == 'warning':
            if diff_hours >= 4:
                interaction['recommendation'] = (
                    f"⚠️ CAUTION: Monitor closely\n\n"
                    f"• Your {diff_hours}-hour gap is adequate.\n"
                    f"• {interaction['description']}\n"
                    f"• {interaction['mechanism']}\n\n"
                    f"✅ MONITORING: {interaction.get('monitoring_advice', 'Watch for side effects')}\n"
                    f"✅ ALTERNATIVES: {interaction.get('alternatives', 'Discuss with doctor')}"
                )
            else:
                interaction['recommendation'] = (
                    f"⚠️ CAUTION - INCREASE GAP\n\n"
                    f"• Only {diff_hours} hours between doses (need 4+ hours).\n"
                    f"• {interaction['description']}\n\n"
                    f"✅ ACTION: Increase spacing to 4+ hours\n"
                    f"✅ MONITOR: {interaction.get('monitoring_advice', 'Watch for side effects')}"
                )
        else:
            # Safe interactions
            interaction['recommendation'] = (
                f"✅ SAFE COMBINATION\n\n"
                f"• No significant interaction expected.\n"
                f"• Your {diff_hours}-hour gap is fine.\n"
                f"• Always consult doctor if you experience unusual symptoms."
            )
        
        interaction['timing_analysis'] = f"{diff_hours} hours apart"
        interaction['timing_status'] = 'good' if diff_hours >= 4 else 'warning'
        
    except Exception as e:
        print(f"⚠️ Timing analysis error: {e}")
        import traceback
        traceback.print_exc()
    
    return interaction

def ml_prediction(drug1, drug2):
    """Predict interaction using ML model"""
    if not ml_available:
        return None
    
    try:
        # Create feature vector
        vec = [0] * len(all_drugs)
        drug1_found = False
        drug2_found = False
        
        for drug in all_drugs:
            if drug.lower() == drug1.lower():
                vec[drug_to_idx[drug]] = 1
                drug1_found = True
                drug1_exact = drug
            if drug.lower() == drug2.lower():
                vec[drug_to_idx[drug]] = 1
                drug2_found = True
                drug2_exact = drug
        
        if not drug1_found or not drug2_found:
            return None
        
        # Check if exact pair exists in database
        pair_key = get_drug_pair_key(drug1_exact, drug2_exact)
        if pair_key in interaction_db:
            db_entry = interaction_db[pair_key]
            return {
                'med1': drug1_exact,
                'med2': drug2_exact,
                'severity': db_entry['severity'],
                'description': db_entry['description'],
                'mechanism': db_entry['mechanism'],
                'recommendation': db_entry['recommendation'],
                'source': 'ml_database'
            }
        
        # Use ML model to predict severity
        X_pred = np.array([vec])
        pred_prob = model.predict_proba(X_pred)[0]
        pred_class = model.predict(X_pred)[0]
        severity = severity_encoder.inverse_transform([pred_class])[0]
        confidence = np.max(pred_prob) * 100
        
        # Generate description based on severity
        if severity == 'danger':
            description = f"Potential dangerous interaction between {drug1_exact} and {drug2_exact}"
            mechanism = "Based on ML model prediction with similar drug pairs"
            recommendation = "Avoid this combination if possible. Consult your doctor immediately."
        elif severity == 'warning':
            description = f"Potential moderate interaction between {drug1_exact} and {drug2_exact}"
            mechanism = "Based on ML model prediction with similar drug pairs"
            recommendation = "Use with caution. Monitor for side effects and consult your doctor."
        else:
            description = f"No significant interaction predicted between {drug1_exact} and {drug2_exact}"
            mechanism = "Based on ML model prediction with similar drug pairs"
            recommendation = "These medications are likely safe to take together, but always consult your doctor."
        
        return {
            'med1': drug1_exact,
            'med2': drug2_exact,
            'severity': severity,
            'description': description,
            'mechanism': mechanism,
            'recommendation': recommendation,
            'confidence': round(confidence, 1),
            'source': 'ml_prediction'
        }
        
    except Exception as e:
        print(f"⚠️ ML prediction error: {e}")
        return None

def llm_prediction(drug1, drug2, dosage1="", dosage2="", timing1="", timing2=""):
    """Get interaction prediction from LLM"""
    if not llm_available:
        return None
    
    prompt = PromptTemplate(
        template="""You are a clinical pharmacology expert. Analyze the potential interaction between these two medications.

Medication 1: {drug1}
Dosage 1: {dosage1}
Timing 1: {timing1}

Medication 2: {drug2}
Dosage 2: {dosage2}
Timing 2: {timing2}

Provide a detailed drug interaction analysis in the following JSON format only, no other text:

{{
  "severity": "danger/warning/safe",
  "description": "Brief description of the interaction",
  "mechanism": "How the drugs interact pharmacologically",
  "recommendation": "Specific advice for the patient",
  "confidence": 85
}}

Base your analysis on standard medical knowledge about drug interactions. Be conservative and accurate.""",
        input_variables=["drug1", "drug2", "dosage1", "dosage2", "timing1", "timing2"]
    )
    
    try:
        response = llm.invoke(prompt.format(
            drug1=drug1, drug2=drug2,
            dosage1=dosage1 or "Not specified",
            dosage2=dosage2 or "Not specified",
            timing1=timing1 or "Not specified",
            timing2=timing2 or "Not specified"
        ))
        
        # Extract JSON from response
        response_text = response.content
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return {
                'med1': drug1,
                'med2': drug2,
                'severity': result.get('severity', 'warning'),
                'description': result.get('description', 'No description available'),
                'mechanism': result.get('mechanism', 'Mechanism unknown'),
                'recommendation': result.get('recommendation', 'Consult your doctor'),
                'confidence': result.get('confidence', 70),
                'source': 'llm_fallback'
            }
    except Exception as e:
        print(f"⚠️ LLM error: {e}")
    
    return None

@app.route('/api/drugs/interactions', methods=['POST'])
def check_interactions():
    try:
        data = request.json
        medications = data.get('medications', [])
        
        if not medications or len(medications) < 2:
            return jsonify({
                'success': False,
                'error': 'Please provide at least 2 medications'
            }), 400
        
        print(f"\n💊 Checking interactions for: {[m['name'] for m in medications]}")
        print(f"⏰ Timings: {[m.get('timing', 'Not specified') for m in medications]}")
        
        results = []
        used_fallback = False
        unknown_drugs = []
        
        # Check each pair
        for med1, med2 in combinations(medications, 2):
            drug1 = med1.get('name', '')
            drug2 = med2.get('name', '')
            timing1 = med1.get('timing', '')
            timing2 = med2.get('timing', '')
            dosage1 = med1.get('dosage', '')
            dosage2 = med2.get('dosage', '')
            
            print(f"🔍 Analyzing pair: {drug1} ({timing1}) + {drug2} ({timing2})")
            
            # Try ML first
            ml_result = ml_prediction(drug1, drug2)
            
            if ml_result:
                result_item = {
                    **ml_result,
                    'dosage1': dosage1,
                    'dosage2': dosage2,
                    'timing1': timing1,
                    'timing2': timing2
                }
                
                # Apply timing analysis to update recommendation
                result_item = analyze_timing_and_update_recommendation(
                    result_item, timing1, timing2
                )
                
                results.append(result_item)
                print(f"   ✅ ML result: {result_item['severity']} (gap: {result_item.get('hours_gap', 'N/A')} hrs)")
            else:
                # Fallback to LLM
                used_fallback = True
                llm_result = llm_prediction(
                    drug1, drug2,
                    dosage1, dosage2,
                    timing1, timing2
                )
                
                if llm_result:
                    result_item = {
                        **llm_result,
                        'dosage1': dosage1,
                        'dosage2': dosage2,
                        'timing1': timing1,
                        'timing2': timing2
                    }
                    
                    # Apply timing analysis to LLM results too
                    result_item = analyze_timing_and_update_recommendation(
                        result_item, timing1, timing2
                    )
                    
                    results.append(result_item)
                    unknown_drugs.extend([drug1, drug2])
                    print(f"   🤖 LLM result: {result_item['severity']} (gap: {result_item.get('hours_gap', 'N/A')} hrs)")
        
        # Count statistics
        danger_count = sum(1 for r in results if r['severity'] == 'danger')
        warning_count = sum(1 for r in results if r['severity'] == 'warning')
        safe_count = sum(1 for r in results if r['severity'] == 'safe')
        
        response_data = {
            'success': True,
            'interactions': results,
            'statistics': {
                'total': len(results),
                'danger': danger_count,
                'warning': warning_count,
                'safe': safe_count
            },
            'used_fallback': used_fallback,
            'unknown_drugs': list(set(unknown_drugs)) if unknown_drugs else None
        }
        
        print(f"✅ Analysis complete: {danger_count} danger, {warning_count} warning, {safe_count} safe")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/drugs/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'ml_available': ml_available,
        'llm_available': llm_available,
        'drugs_count': len(all_drugs) if ml_available else 0,
        'interactions_count': len(interaction_db) if ml_available else 0
    })

if __name__ == '__main__':
    print("🚀 Drug Interaction Checker starting on port 5004...")
    app.run(host='0.0.0.0', port=5004, debug=True)
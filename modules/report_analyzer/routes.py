# modules/report_analyzer/routes.py
from flask import Blueprint, request, jsonify, current_app
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add module path to system path
sys.path.append(str(Path(__file__).parent))

from agents.model_manager import ModelManager
from utils.pdf_extractor import extract_text_from_pdf
from utils.validators import validate_pdf_file
from config.prompts import SPECIALIST_PROMPTS

# Load environment variables
load_dotenv()

# Create blueprint
report_analyzer_bp = Blueprint('report_analyzer', __name__, url_prefix='/api/report-analyzer')

# Initialize ModelManager
try:
    model_manager = ModelManager()
except ValueError as e:
    print(f"⚠️ Warning: ModelManager initialization failed: {e}")
    model_manager = None


# Find the analyze_report function and replace it with this:

@report_analyzer_bp.route('/analyze', methods=['POST'])
def analyze_report():
    """
    API endpoint to analyze medical report
    Expects:
        - patient_name (form field)
        - age (form field)
        - gender (form field)
        - pdf_file (file upload)
        - userId (form field)
        - userRole (form field) - 'patient' or 'doctor'
    """
    
    if not model_manager:
        return jsonify({
            'success': False,
            'error': 'AI model not initialized. Check GROQ_API_KEY'
        }), 500
    
    try:
        # Get form data
        patient_name = request.form.get('patient_name', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        user_id = request.form.get('userId', '').strip()
        user_role = request.form.get('userRole', 'patient').strip()  # Get user role
        
        # Validate input
        if not all([patient_name, age, gender]):
            return jsonify({
                'success': False,
                'error': 'Please fill in all patient details'
            }), 400
        
        # Get PDF file
        if 'pdf_file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No PDF file uploaded'
            }), 400
            
        pdf_file = request.files['pdf_file']
        
        if pdf_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Validate PDF
        is_valid, validation_error = validate_pdf_file(pdf_file)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': validation_error
            }), 400
        
        # Extract text from PDF
        extracted_text = extract_text_from_pdf(pdf_file)
        
        if extracted_text.startswith("Error:"):
            return jsonify({
                'success': False,
                'error': extracted_text.replace("Error: ", "")
            }), 400
        
        # Prepare data for AI
        analysis_data = {
            "patient_name": patient_name,
            "age": age,
            "gender": gender,
            "report": extracted_text
        }
        
        # Choose prompt based on user role
        if user_role == 'doctor':
            system_prompt = SPECIALIST_PROMPTS["doctor_analyst"]
            print(f"👨‍⚕️ Using DOCTOR prompt for analysis")
        else:
            system_prompt = SPECIALIST_PROMPTS["patient_analyst"]
            print(f"👤 Using PATIENT prompt for analysis")
        
        # Run AI analysis
        result = model_manager.generate_analysis(
            data=analysis_data,
            system_prompt=system_prompt
        )
        
        if result["success"]:
            return jsonify({
                'success': True,
                'analysis': result["content"],
                'model_used': result.get("model_used", "unknown"),
                'user_role': user_role,  # Return role for confirmation
                'extracted_text_preview': extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result["error"]
            }), 500
            
    except Exception as e:
        print(f"❌ Server error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500
@report_analyzer_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_initialized': model_manager is not None
    })
# ~/Desktop/4th Major/project/medical-report-analysis/modules/report_analyzer/app.py

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
load_dotenv()

# Check for API key early
if not os.getenv("GROQ_API_KEY"):
    raise EnvironmentError("GROQ_API_KEY is not set in the environment or .env file.")

# Import the blueprint from routes.py
from routes import report_analyzer_bp

# Import core components for the web interface
from agents.model_manager import ModelManager
from utils.pdf_extractor import extract_text_from_pdf
from utils.validators import validate_pdf_file
from config.prompts import SPECIALIST_PROMPTS

# Initialize Flask App
app = Flask(__name__)

# Set maximum content length for uploads (20 MB)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

# Register the blueprint from routes.py
app.register_blueprint(report_analyzer_bp)

# Initialize ModelManager for web interface
try:
    model_manager = ModelManager()
    print("✅ ModelManager initialized successfully")
except ValueError as e:
    print(f"⚠️ Warning: {e}")
    model_manager = None

@app.route('/', methods=['GET', 'POST'])
def analyze_report():
    """Handles the form submission, PDF processing, and AI analysis."""
    analysis_result = None
    extracted_text = None
    error_message = None
    
    if request.method == 'POST':
        # 1. Get patient data from form fields
        patient_name = request.form.get('patient_name', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        
        # Basic input validation
        if not all([patient_name, age, gender]):
            error_message = "Please fill in all patient details (Name, Age, Gender)."
            return render_template('index.html', error=error_message)
        
        # 2. Handle file upload
        pdf_file = request.files.get('pdf_file')
        if not pdf_file or pdf_file.filename == '':
            error_message = "Please upload a medical report PDF."
            return render_template('index.html', error=error_message)
        
        # Check basic file validity
        is_valid, validation_error = validate_pdf_file(pdf_file)
        if not is_valid:
            error_message = validation_error
            return render_template('index.html', error=error_message)
        
        try:
            # 3. Extract text from PDF
            extracted_text = extract_text_from_pdf(pdf_file)
            
            if extracted_text.startswith("Error:"):
                error_message = extracted_text.replace("Error: ", "")
                return render_template('index.html', error=error_message)
            
            # 4. Prepare data for AI analysis
            analysis_data = {
                "patient_name": patient_name,
                "age": age,
                "gender": gender,
                "report": extracted_text
            }
            
            # 5. Run AI analysis
            result = model_manager.generate_analysis(
                data=analysis_data,
                system_prompt=SPECIALIST_PROMPTS["patient_analyst"]
            )
            
            if result["success"]:
                analysis_result = result["content"]
            else:
                error_message = result["error"]
            
        except Exception as e:
            error_message = f"An unexpected server error occurred: {str(e)}"
    
    # Render the main template with or without results/errors
    return render_template(
        'index.html',
        analysis_result=analysis_result,
        extracted_text=extracted_text,
        error=error_message
    )

# API Status endpoint
@app.route('/api/status', methods=['GET'])
def api_status():
    """Check if API is available"""
    return jsonify({
        'status': 'running',
        'model_initialized': model_manager is not None,
        'api_endpoints': {
            'health': '/api/report-analyzer/health',
            'analyze': '/api/report-analyzer/analyze'
        }
    })

if __name__ == '__main__':
    import sys
    port = 5001  # Default port
    if len(sys.argv) > 2 and sys.argv[1] == '--port':
        port = int(sys.argv[2])
    print(f"🚀 Report Analyzer running on port {port}")
    print(f"📝 Web Interface: http://localhost:{port}/")
    print(f"📝 API Health: http://localhost:{port}/api/report-analyzer/health")
    print(f"📝 API Analyze: http://localhost:{port}/api/report-analyzer/analyze")
    app.run(debug=True, port=port, host='0.0.0.0')
import re
from typing import Tuple, Optional, Any

# Flask Max Upload Size is configured in app.py, but we keep this constant for content validation
MAX_UPLOAD_SIZE_MB = 20

def validate_pdf_file(file: Any) -> Tuple[bool, Optional[str]]:
    """Validate PDF file size and type (basic check)."""
    # Note: Flask handles max file size via config, but we keep this function structure.
    if not file:
        return False, "No file uploaded"
        
    # Check file type based on filename/mimeType (less reliable than file signature but useful)
    if not file.filename.lower().endswith('.pdf'):
        return False, "Invalid file type. Please upload a PDF file"
        
    return True, None

def validate_pdf_content(text: str) -> Tuple[bool, Optional[str]]:
    """Validate if the extracted content appears to be a medical report."""
    # Common medical report indicators
    medical_terms = [
        'blood', 'test', 'report', 'laboratory', 'lab', 'patient', 'specimen',
        'reference range', 'analysis', 'results', 'medical', 'diagnostic',
        'hemoglobin', 'wbc', 'rbc', 'platelet', 'glucose', 'creatinine'
    ]
    
    # Validate minimum text length
    if len(text.strip()) < 50:
        return False, "Extracted text is too short. Please ensure the PDF contains valid text."
    
    # Check for medical terms
    text_lower = text.lower()
    term_matches = sum(1 for term in medical_terms if term in text_lower)
    
    if term_matches < 3:
        return False, "The uploaded file doesn't appear to be a medical report. Please upload a valid medical report."
    
    return True, None
import pdfplumber
from werkzeug.datastructures import FileStorage
from utils.validators import validate_pdf_file, validate_pdf_content

# Define a reasonable page limit for large reports
MAX_PDF_PAGES = 50

def extract_text_from_pdf(pdf_file: FileStorage) -> str:
    """Extract and validate text from PDF file."""
    
    # Validate file before reading
    is_valid, error = validate_pdf_file(pdf_file)
    if not is_valid:
        return f"Error: {error}"

    try:
        text = ""
        # pdfplumber can open file objects directly (pdf_file.stream)
        with pdfplumber.open(pdf_file.stream) as pdf:
            if len(pdf.pages) > MAX_PDF_PAGES:
                return f"Error: PDF exceeds maximum page limit of {MAX_PDF_PAGES}"
                
            for page in pdf.pages:
                extracted = page.extract_text()
                if not extracted:
                    # Could happen if the PDF is scanned without OCR
                    return "Error: Could not extract text from PDF. Please ensure it's not a scanned image."
                text += extracted + "\n"
        
        # Validate extracted content
        is_valid, error = validate_pdf_content(text)
        if not is_valid:
            return f"Error: {error}"
            
        return text
        
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"
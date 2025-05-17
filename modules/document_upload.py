"""
Document Upload Module

This module provides document upload functionality with AI-powered OCR to extract
tax-relevant information from uploaded documents.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import User, BusinessProfile
from app.access_control import requires_access_level
from ai.openai_interface import get_openai_response, analyze_image
import os
import json
import logging
import uuid
import base64
from datetime import datetime
import pytesseract
from PIL import Image
import io
import re
import fitz  # PyMuPDF for PDF processing

# Create blueprint
documents_bp = Blueprint("documents", __name__, url_prefix="/documents")

# Configure upload paths
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Ensure user folders exist
def get_user_folder(user_id):
    """Get or create a user-specific upload folder"""
    user_folder = os.path.join(UPLOAD_FOLDER, str(user_id))
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    return user_folder

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}

def allowed_file(filename):
    """Check if a filename has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@documents_bp.route("/")
@login_required
def index():
    """Document upload and management page"""
    uploads = get_user_documents(current_user.id)
    recent_uploads = uploads[:5] if uploads else []
    
    return render_template(
        "documents/index.html",
        recent_uploads=recent_uploads,
        document_count=len(uploads),
        document_categories=get_document_categories()
    )

@documents_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    """Handle document upload"""
    if request.method == "POST":
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        category = request.form.get('category', 'other')
        
        if file and allowed_file(file.filename):
            # Save file with secure filename
            original_filename = secure_filename(file.filename)
            
            # Generate unique filename to avoid collisions
            unique_id = str(uuid.uuid4())
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{unique_id}.{file_extension}"
            
            # Get user folder
            user_folder = get_user_folder(current_user.id)
            file_path = os.path.join(user_folder, unique_filename)
            
            # Save the file
            file.save(file_path)
            
            # Process the document and extract information
            document_data = process_document(file_path, file_extension)
            
            # Save document metadata
            save_document_metadata(
                user_id=current_user.id,
                original_filename=original_filename,
                unique_filename=unique_filename,
                category=category,
                file_extension=file_extension,
                file_path=file_path,
                extracted_data=document_data
            )
            
            flash(f'File {original_filename} uploaded successfully!', 'success')
            
            # If it's an AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True, 
                    'message': f'File {original_filename} uploaded successfully!',
                    'document_data': document_data
                })
            
            return redirect(url_for('documents.index'))
        
        flash('File type not allowed', 'danger')
        return redirect(request.url)
    
    return render_template(
        "documents/upload.html",
        document_categories=get_document_categories()
    )

@documents_bp.route("/view/<string:doc_id>")
@login_required
def view_document(doc_id):
    """View document details and extracted information"""
    document = get_document_metadata(doc_id, current_user.id)
    
    if not document:
        flash('Document not found', 'danger')
        return redirect(url_for('documents.index'))
    
    return render_template(
        "documents/view.html",
        document=document
    )

@documents_bp.route("/delete/<string:doc_id>", methods=["POST"])
@login_required
def delete_document(doc_id):
    """Delete a document"""
    document = get_document_metadata(doc_id, current_user.id)
    
    if not document:
        flash('Document not found', 'danger')
        return redirect(url_for('documents.index'))
    
    # Delete the file
    if os.path.exists(document['file_path']):
        os.remove(document['file_path'])
    
    # Remove metadata
    delete_document_metadata(doc_id, current_user.id)
    
    flash('Document deleted successfully', 'success')
    
    # If it's an AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    return redirect(url_for('documents.index'))

@documents_bp.route("/category/<string:category>")
@login_required
def category_documents(category):
    """View documents in a specific category"""
    uploads = get_user_documents(current_user.id, category=category)
    
    return render_template(
        "documents/category.html",
        uploads=uploads,
        category=category,
        category_info=get_document_categories().get(category, {'name': category.title()})
    )

@documents_bp.route("/analyze/<string:doc_id>")
@login_required
@requires_access_level("ai_sorted_uploads")
def analyze_document(doc_id):
    """Run AI analysis on a document to extract additional information"""
    document = get_document_metadata(doc_id, current_user.id)
    
    if not document:
        flash('Document not found', 'danger')
        return redirect(url_for('documents.index'))
    
    # Run enhanced AI analysis
    analysis_results = run_ai_analysis(document['file_path'], document['file_extension'])
    
    # Update document metadata with analysis results
    update_document_metadata(doc_id, current_user.id, {
        'ai_analysis': analysis_results,
        'analyzed_at': datetime.now().isoformat()
    })
    
    flash('Document analysis completed', 'success')
    return redirect(url_for('documents.view_document', doc_id=doc_id))

def process_document(file_path, file_extension):
    """
    Process a document to extract information
    
    Args:
        file_path: Path to the uploaded file
        file_extension: File extension
        
    Returns:
        Dictionary with extracted information
    """
    extracted_text = ""
    detected_type = "unknown"
    extracted_data = {}
    
    try:
        # Extract text using the appropriate method based on file type
        if file_extension == 'pdf':
            extracted_text = extract_text_from_pdf(file_path)
        else:  # Image file
            extracted_text = extract_text_from_image(file_path)
        
        # Detect document type based on content
        detected_type = detect_document_type(extracted_text)
        
        # Extract relevant information based on document type
        extracted_data = extract_information(extracted_text, detected_type)
        
    except Exception as e:
        logging.error(f"Error processing document: {e}")
        extracted_data = {"error": str(e)}
    
    return {
        "extracted_text": extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text,
        "detected_type": detected_type,
        "extracted_data": extracted_data
    }

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text as a string
    """
    extracted_text = ""
    
    try:
        # Open the PDF
        pdf_document = fitz.open(file_path)
        
        # Extract text from each page
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            extracted_text += page.get_text()
        
        pdf_document.close()
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        raise
    
    return extracted_text

def extract_text_from_image(file_path):
    """
    Extract text from an image file using OCR
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Extracted text as a string
    """
    try:
        # Open the image using PIL
        image = Image.open(file_path)
        
        # Use pytesseract for OCR
        extracted_text = pytesseract.image_to_string(image)
        
        return extracted_text
    except Exception as e:
        logging.error(f"Error extracting text from image: {e}")
        raise

def detect_document_type(text):
    """
    Detect the type of document based on its content
    
    Args:
        text: Extracted text from the document
        
    Returns:
        String indicating the document type
    """
    text_lower = text.lower()
    
    # Check for various document types
    if "form w-2" in text_lower or "wage and tax statement" in text_lower:
        return "w2"
    elif "form 1099-" in text_lower:
        if "1099-misc" in text_lower or "miscellaneous income" in text_lower:
            return "1099_misc"
        elif "1099-nec" in text_lower or "nonemployee compensation" in text_lower:
            return "1099_nec"
        else:
            return "1099"
    elif "schedule c" in text_lower or "profit or loss from business" in text_lower:
        return "schedule_c"
    elif "bank statement" in text_lower or "account statement" in text_lower:
        return "bank_statement"
    elif "invoice" in text_lower or "bill to" in text_lower:
        return "invoice"
    elif "receipt" in text_lower or "payment received" in text_lower:
        return "receipt"
    elif "expense report" in text_lower:
        return "expense_report"
    
    # Default to unknown
    return "unknown"

def extract_information(text, document_type):
    """
    Extract relevant information based on the document type
    
    Args:
        text: Extracted text from the document
        document_type: Detected document type
        
    Returns:
        Dictionary with extracted information
    """
    extracted_info = {}
    
    if document_type == "w2":
        # Extract W-2 information
        extracted_info["employer_ein"] = extract_pattern(text, r'Employer identification number\s*(?:\(EIN\))?\s*(\d{2}-\d{7})')
        extracted_info["wages"] = extract_pattern(text, r'Wages, tips, other comp\.?\s*\$?([0-9,.]+)')
        extracted_info["federal_income_tax"] = extract_pattern(text, r'Federal income tax withheld\s*\$?([0-9,.]+)')
        extracted_info["social_security_wages"] = extract_pattern(text, r'Social security wages\s*\$?([0-9,.]+)')
        extracted_info["social_security_tax"] = extract_pattern(text, r'Social security tax withheld\s*\$?([0-9,.]+)')
        extracted_info["medicare_wages"] = extract_pattern(text, r'Medicare wages and tips\s*\$?([0-9,.]+)')
        extracted_info["medicare_tax"] = extract_pattern(text, r'Medicare tax withheld\s*\$?([0-9,.]+)')
        
    elif document_type in ["1099_misc", "1099_nec", "1099"]:
        # Extract 1099 information
        extracted_info["payer_tin"] = extract_pattern(text, r'PAYER\'?S?\s*(?:TIN|taxpayer\s*identification\s*number)\s*(\d{2}-\d{7})')
        extracted_info["recipient_tin"] = extract_pattern(text, r'RECIPIENT\'?S?\s*(?:TIN|taxpayer\s*identification\s*number)\s*(\d{2}-\d{7}|\d{3}-\d{2}-\d{4})')
        
        if document_type == "1099_nec":
            extracted_info["nonemployee_compensation"] = extract_pattern(text, r'Nonemployee compensation\s*\$?([0-9,.]+)')
        elif document_type == "1099_misc":
            extracted_info["rents"] = extract_pattern(text, r'Rents\s*\$?([0-9,.]+)')
            extracted_info["royalties"] = extract_pattern(text, r'Royalties\s*\$?([0-9,.]+)')
            extracted_info["other_income"] = extract_pattern(text, r'Other income\s*\$?([0-9,.]+)')
        
    elif document_type == "bank_statement":
        # Extract bank statement information
        extracted_info["account_number"] = extract_pattern(text, r'Account\s*(?:Number|#)\s*[:.]\s*(?:[X*]+)?(\d{4,})')
        extracted_info["statement_period"] = extract_pattern(text, r'Statement\s*Period\s*[:.]\s*([A-Za-z0-9 ,\-/]+)')
        extracted_info["opening_balance"] = extract_pattern(text, r'(?:Opening|Beginning)\s*Balance\s*[:.]\s*\$?([0-9,.]+)')
        extracted_info["closing_balance"] = extract_pattern(text, r'(?:Closing|Ending)\s*Balance\s*[:.]\s*\$?([0-9,.]+)')
        
    elif document_type == "invoice":
        # Extract invoice information
        extracted_info["invoice_number"] = extract_pattern(text, r'(?:Invoice|Bill|Reference)\s*(?:Number|No|#)\s*[:.]\s*([A-Za-z0-9\-]+)')
        extracted_info["invoice_date"] = extract_pattern(text, r'(?:Invoice|Bill)\s*Date\s*[:.]\s*([A-Za-z0-9 ,\-/]+)')
        extracted_info["due_date"] = extract_pattern(text, r'(?:Due|Payment)\s*Date\s*[:.]\s*([A-Za-z0-9 ,\-/]+)')
        extracted_info["total_amount"] = extract_pattern(text, r'(?:Total|Amount Due|Balance Due)\s*[:.]\s*\$?([0-9,.]+)')
        
    elif document_type == "receipt":
        # Extract receipt information
        extracted_info["receipt_date"] = extract_pattern(text, r'(?:Date|Receipt Date)\s*[:.]\s*([A-Za-z0-9 ,\-/]+)')
        extracted_info["total_amount"] = extract_pattern(text, r'(?:Total|Amount|Total Amount|Grand Total)\s*[:.]\s*\$?([0-9,.]+)')
        extracted_info["payment_method"] = extract_pattern(text, r'(?:Payment Method|Paid By|Method)\s*[:.]\s*([A-Za-z0-9 ]+)')
    
    return extracted_info

def extract_pattern(text, pattern):
    """
    Extract information using a regex pattern
    
    Args:
        text: Text to search
        pattern: Regex pattern with one capturing group
        
    Returns:
        Extracted string or None
    """
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def run_ai_analysis(file_path, file_extension):
    """
    Run enhanced AI analysis on a document
    
    Args:
        file_path: Path to the file
        file_extension: File extension
        
    Returns:
        Dictionary with AI analysis results
    """
    try:
        # For image files, use OpenAI Vision API
        if file_extension in ['png', 'jpg', 'jpeg', 'tiff', 'bmp']:
            with open(file_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                analysis = analyze_image(base64_image)
                
                return {
                    "ai_description": analysis,
                    "document_summary": extract_document_summary_from_analysis(analysis)
                }
        
        # For PDF files, extract text and use OpenAI text analysis
        elif file_extension == 'pdf':
            extracted_text = extract_text_from_pdf(file_path)
            
            # Use OpenAI to analyze the document content
            system_message = """
            You are an AI assistant specialized in analyzing tax and financial documents.
            Analyze the provided document text and extract key information relevant for tax purposes.
            Focus on identifying the document type, key financial figures, dates, and tax implications.
            """
            
            user_message = f"""
            Please analyze this document text and provide:
            1. Document type identification
            2. Key financial figures (amounts, income, expenses, etc.)
            3. Relevant dates
            4. Potential tax implications
            5. Any missing information that would be needed for tax filing
            
            Document text:
            {extracted_text[:4000]}  # Limit text length to avoid token limits
            """
            
            analysis = get_openai_response(system_message, user_message)
            
            return {
                "ai_analysis": analysis,
                "document_summary": extract_document_summary_from_analysis(analysis)
            }
    
    except Exception as e:
        logging.error(f"Error in AI analysis: {e}")
        return {"error": str(e)}
    
    return {"message": "No enhanced analysis available for this document type"}

def extract_document_summary_from_analysis(analysis):
    """
    Extract a concise summary from the AI analysis
    
    Args:
        analysis: AI analysis text
        
    Returns:
        Concise summary string
    """
    # Use a simpler approach - extract the first paragraph or sentence
    if not analysis:
        return "No summary available"
    
    # Try to get the first paragraph
    paragraphs = analysis.split('\n\n')
    if paragraphs:
        first_para = paragraphs[0].strip()
        if len(first_para) > 10:  # Ensure it's meaningful
            return first_para
    
    # Fall back to first sentence
    sentences = analysis.split('.')
    if sentences:
        return sentences[0].strip() + "."
    
    return "No summary available"

def get_document_categories():
    """
    Get document categories for organization
    
    Returns:
        Dictionary of document categories and their descriptions
    """
    return {
        "income": {
            "name": "Income Documents",
            "description": "W-2s, 1099s, and other income documentation",
            "icon": "fas fa-money-bill-wave"
        },
        "expenses": {
            "name": "Expense Documents",
            "description": "Receipts, invoices, and expense documentation",
            "icon": "fas fa-receipt"
        },
        "banking": {
            "name": "Banking Documents",
            "description": "Bank statements, canceled checks, and financial records",
            "icon": "fas fa-university"
        },
        "tax_returns": {
            "name": "Tax Returns",
            "description": "Previous tax returns and filing documentation",
            "icon": "fas fa-file-invoice-dollar"
        },
        "business": {
            "name": "Business Documents",
            "description": "Business formation, licenses, and operational documents",
            "icon": "fas fa-building"
        },
        "other": {
            "name": "Other Documents",
            "description": "Miscellaneous tax-related documentation",
            "icon": "fas fa-folder"
        }
    }

def save_document_metadata(user_id, original_filename, unique_filename, category, file_extension, file_path, extracted_data):
    """
    Save document metadata to storage
    
    In a production environment, this would save to a database.
    For simplicity, we'll use a JSON file-based storage.
    
    Args:
        user_id: User ID
        original_filename: Original filename
        unique_filename: Unique filename on disk
        category: Document category
        file_extension: File extension
        file_path: Path to the stored file
        extracted_data: Data extracted from the document
    """
    # Create metadata
    doc_id = str(uuid.uuid4())
    metadata = {
        "id": doc_id,
        "user_id": user_id,
        "original_filename": original_filename,
        "unique_filename": unique_filename,
        "category": category,
        "file_extension": file_extension,
        "file_path": file_path,
        "upload_date": datetime.now().isoformat(),
        "extracted_data": extracted_data
    }
    
    # Get the metadata storage file
    metadata_file = get_metadata_file(user_id)
    
    # Load existing metadata
    all_metadata = []
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r') as f:
                all_metadata = json.load(f)
        except:
            all_metadata = []
    
    # Add new metadata
    all_metadata.append(metadata)
    
    # Save updated metadata
    with open(metadata_file, 'w') as f:
        json.dump(all_metadata, f, indent=2)
    
    return doc_id

def get_metadata_file(user_id):
    """Get the path to the user's metadata file"""
    user_folder = get_user_folder(user_id)
    return os.path.join(user_folder, "metadata.json")

def get_user_documents(user_id, category=None):
    """
    Get all documents for a user
    
    Args:
        user_id: User ID
        category: Optional category filter
        
    Returns:
        List of document metadata
    """
    metadata_file = get_metadata_file(user_id)
    
    if not os.path.exists(metadata_file):
        return []
    
    try:
        with open(metadata_file, 'r') as f:
            all_metadata = json.load(f)
        
        # Apply category filter if specified
        if category:
            return [doc for doc in all_metadata if doc['category'] == category]
        
        return all_metadata
    except:
        return []

def get_document_metadata(doc_id, user_id):
    """
    Get metadata for a specific document
    
    Args:
        doc_id: Document ID
        user_id: User ID (for security)
        
    Returns:
        Document metadata or None if not found
    """
    all_docs = get_user_documents(user_id)
    
    for doc in all_docs:
        if doc['id'] == doc_id and doc['user_id'] == user_id:
            return doc
    
    return None

def update_document_metadata(doc_id, user_id, updates):
    """
    Update metadata for a specific document
    
    Args:
        doc_id: Document ID
        user_id: User ID (for security)
        updates: Dictionary of metadata fields to update
        
    Returns:
        True if successful, False otherwise
    """
    metadata_file = get_metadata_file(user_id)
    
    if not os.path.exists(metadata_file):
        return False
    
    try:
        with open(metadata_file, 'r') as f:
            all_metadata = json.load(f)
        
        # Find and update the document
        for i, doc in enumerate(all_metadata):
            if doc['id'] == doc_id and doc['user_id'] == user_id:
                # Update fields
                for key, value in updates.items():
                    all_metadata[i][key] = value
                
                # Save updated metadata
                with open(metadata_file, 'w') as f:
                    json.dump(all_metadata, f, indent=2)
                
                return True
        
        return False
    except:
        return False

def delete_document_metadata(doc_id, user_id):
    """
    Delete metadata for a specific document
    
    Args:
        doc_id: Document ID
        user_id: User ID (for security)
        
    Returns:
        True if successful, False otherwise
    """
    metadata_file = get_metadata_file(user_id)
    
    if not os.path.exists(metadata_file):
        return False
    
    try:
        with open(metadata_file, 'r') as f:
            all_metadata = json.load(f)
        
        # Filter out the document to delete
        updated_metadata = [doc for doc in all_metadata if not (doc['id'] == doc_id and doc['user_id'] == user_id)]
        
        # Save updated metadata
        with open(metadata_file, 'w') as f:
            json.dump(updated_metadata, f, indent=2)
        
        return True
    except:
        return False
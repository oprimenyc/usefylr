import os
import io
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from app.models import TaxForm, IRSLetter

# Directory for storing generated PDFs
PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'pdfs')
os.makedirs(PDF_DIR, exist_ok=True)

def generate_tax_form_pdf(tax_form):
    """Generate a PDF for a tax form"""
    try:
        # Create a unique filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"form_{tax_form.form_type.value}_{tax_form.user_id}_{timestamp}.pdf"
        filepath = os.path.join(PDF_DIR, filename)
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Build the PDF content
        elements = []
        
        # Add title
        form_title = f"Form {tax_form.form_type.value} - Tax Year {tax_form.tax_year}"
        elements.append(Paragraph(form_title, title_style))
        elements.append(Spacer(1, 12))
        
        # Add generation info
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        elements.append(Spacer(1, 24))
        
        # Add form data
        form_data = tax_form.data
        if form_data:
            # Group data by section (assuming it's organized somehow)
            if tax_form.form_type.value == "1120":
                # Process 1120 form
                elements.append(Paragraph("U.S. Corporation Income Tax Return", heading_style))
                elements.append(Spacer(1, 12))
                
                # Basic info section
                elements.append(Paragraph("Basic Information", heading_style))
                data = [
                    ["Company Name:", form_data.get("company_name", "")],
                    ["EIN:", form_data.get("ein", "")],
                    ["Address:", form_data.get("address", "")],
                    ["Date of Incorporation:", form_data.get("incorporation_date", "")],
                    ["Tax Year:", form_data.get("tax_year", "")]
                ]
                t = Table(data, colWidths=[150, 300])
                t.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 24))
                
                # Income section
                elements.append(Paragraph("Income", heading_style))
                data = [
                    ["Gross Receipts or Sales:", f"${form_data.get('gross_receipts', '0')}"],
                    ["Returns and Allowances:", f"${form_data.get('returns_allowances', '0')}"],
                    ["Other Income:", f"${form_data.get('other_income', '0')}"]
                ]
                t = Table(data, colWidths=[200, 250])
                t.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 24))
                
                # Deductions section
                elements.append(Paragraph("Deductions", heading_style))
                data = [
                    ["Salaries and Wages:", f"${form_data.get('salaries_wages', '0')}"],
                    ["Repairs and Maintenance:", f"${form_data.get('repairs_maintenance', '0')}"],
                    ["Rents:", f"${form_data.get('rents', '0')}"],
                    ["Taxes and Licenses:", f"${form_data.get('taxes_licenses', '0')}"],
                    ["Interest:", f"${form_data.get('interest', '0')}"],
                    ["Depreciation:", f"${form_data.get('depreciation', '0')}"],
                    ["Other Deductions:", f"${form_data.get('other_deductions', '0')}"]
                ]
                t = Table(data, colWidths=[200, 250])
                t.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
                ]))
                elements.append(t)
                
            elif tax_form.form_type.value == "1065":
                # Process 1065 form
                elements.append(Paragraph("U.S. Return of Partnership Income", heading_style))
                elements.append(Spacer(1, 12))
                
                # Partnership info section
                elements.append(Paragraph("Partnership Information", heading_style))
                data = [
                    ["Partnership Name:", form_data.get("partnership_name", "")],
                    ["EIN:", form_data.get("ein", "")],
                    ["Address:", form_data.get("address", "")],
                    ["Date Partnership Formed:", form_data.get("formation_date", "")],
                    ["Tax Year:", form_data.get("tax_year", "")]
                ]
                t = Table(data, colWidths=[150, 300])
                t.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 24))
                
                # Income section
                elements.append(Paragraph("Income", heading_style))
                data = [
                    ["Gross Receipts or Sales:", f"${form_data.get('gross_receipts', '0')}"],
                    ["Cost of Goods Sold:", f"${form_data.get('cost_of_goods', '0')}"],
                    ["Other Income:", f"${form_data.get('other_income', '0')}"]
                ]
                t = Table(data, colWidths=[200, 250])
                t.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 24))
                
                # Deductions section
                elements.append(Paragraph("Deductions", heading_style))
                data = [
                    ["Salaries and Wages:", f"${form_data.get('salaries_wages', '0')}"],
                    ["Guaranteed Payments to Partners:", f"${form_data.get('guaranteed_payments', '0')}"],
                    ["Repairs and Maintenance:", f"${form_data.get('repairs_maintenance', '0')}"],
                    ["Rent:", f"${form_data.get('rent', '0')}"],
                    ["Taxes and Licenses:", f"${form_data.get('taxes_licenses', '0')}"],
                    ["Interest:", f"${form_data.get('interest', '0')}"],
                    ["Depreciation:", f"${form_data.get('depreciation', '0')}"],
                    ["Other Deductions:", f"${form_data.get('other_deductions', '0')}"]
                ]
                t = Table(data, colWidths=[200, 250])
                t.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
                ]))
                elements.append(t)
                
            elif tax_form.form_type.value == "Schedule C":
                # Process Schedule C form
                elements.append(Paragraph("Profit or Loss From Business (Sole Proprietorship)", heading_style))
                elements.append(Spacer(1, 12))
                
                # Business info section
                elements.append(Paragraph("Business Information", heading_style))
                data = [
                    ["Business Name:", form_data.get("business_name", "")],
                    ["Business Code:", form_data.get("business_code", "")],
                    ["SSN:", form_data.get("ssn", "")],
                    ["Address:", form_data.get("address", "")],
                    ["Tax Year:", form_data.get("tax_year", "")]
                ]
                t = Table(data, colWidths=[150, 300])
                t.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 24))
                
                # Income section
                elements.append(Paragraph("Income", heading_style))
                data = [
                    ["Gross Receipts or Sales:", f"${form_data.get('gross_receipts', '0')}"],
                    ["Returns and Allowances:", f"${form_data.get('returns_allowances', '0')}"],
                    ["Other Income:", f"${form_data.get('other_income', '0')}"]
                ]
                t = Table(data, colWidths=[200, 250])
                t.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 24))
                
                # Expenses section
                elements.append(Paragraph("Expenses", heading_style))
                data = [
                    ["Advertising:", f"${form_data.get('advertising', '0')}"],
                    ["Car and Truck Expenses:", f"${form_data.get('car_expenses', '0')}"],
                    ["Commissions and Fees:", f"${form_data.get('commissions', '0')}"],
                    ["Depreciation:", f"${form_data.get('depreciation', '0')}"],
                    ["Insurance:", f"${form_data.get('insurance', '0')}"],
                    ["Legal and Professional Services:", f"${form_data.get('professional_fees', '0')}"],
                    ["Office Expenses:", f"${form_data.get('office_expenses', '0')}"],
                    ["Rent - Equipment:", f"${form_data.get('rent_equipment', '0')}"],
                    ["Rent - Property:", f"${form_data.get('rent_property', '0')}"],
                    ["Supplies:", f"${form_data.get('supplies', '0')}"],
                    ["Taxes and Licenses:", f"${form_data.get('taxes_licenses', '0')}"],
                    ["Travel:", f"${form_data.get('travel', '0')}"],
                    ["Meals:", f"${form_data.get('meals', '0')}"],
                    ["Utilities:", f"${form_data.get('utilities', '0')}"],
                    ["Wages:", f"${form_data.get('wages', '0')}"],
                    ["Other Expenses:", f"${form_data.get('other_expenses', '0')}"]
                ]
                t = Table(data, colWidths=[200, 250])
                t.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
                ]))
                elements.append(t)
        
        # Add disclaimer
        elements.append(Spacer(1, 36))
        disclaimer_text = "DISCLAIMER: This document is for informational purposes only and is not an official IRS form. Please use this as a guide to complete your official tax filing. Consult a tax professional for tax advice."
        elements.append(Paragraph(disclaimer_text, ParagraphStyle(name='Disclaimer', fontName='Helvetica', fontSize=8, textColor=colors.red)))
        
        # Build the PDF
        doc.build(elements)
        
        return filename
    except Exception as e:
        logging.error(f"Error generating tax form PDF: {str(e)}")
        return None

def generate_irs_letter_pdf(letter):
    """Generate a PDF for an IRS letter"""
    try:
        # Create a unique filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"letter_{letter.letter_type.value}_{letter.user_id}_{timestamp}.pdf"
        filepath = os.path.join(PDF_DIR, filename)
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Build the PDF content
        elements = []
        
        # Get letter data
        letter_data = letter.data
        
        if letter.letter_type.value == "penalty_abatement":
            # Penalty Abatement Letter
            elements.append(Paragraph("Request for Penalty Abatement", title_style))
            elements.append(Spacer(1, 24))
            
            # Sender info
            elements.append(Paragraph(letter_data.get("taxpayer_name", ""), normal_style))
            elements.append(Paragraph(letter_data.get("taxpayer_address", ""), normal_style))
            elements.append(Paragraph(f"EIN/SSN: {letter_data.get('taxpayer_ein', '')}", normal_style))
            elements.append(Spacer(1, 24))
            
            # Date
            elements.append(Paragraph(f"Date: {letter_data.get('date', '')}", normal_style))
            elements.append(Spacer(1, 12))
            
            # Recipient - IRS
            elements.append(Paragraph("Internal Revenue Service", normal_style))
            elements.append(Paragraph("Penalty Abatement Request", normal_style))
            elements.append(Paragraph("[IRS Address Placeholder]", normal_style))
            elements.append(Spacer(1, 24))
            
            # Subject
            elements.append(Paragraph(f"Subject: Request for Abatement of Penalty - Tax Year {letter_data.get('tax_year', '')}", heading_style))
            elements.append(Spacer(1, 12))
            
            # Greeting
            elements.append(Paragraph("To Whom It May Concern:", normal_style))
            elements.append(Spacer(1, 12))
            
            # Body
            body_text = f"""I am writing to request an abatement of the penalty in the amount of ${letter_data.get('penalty_amount', '0')} 
            assessed for the tax year {letter_data.get('tax_year', '')} due to {letter_data.get('reason', '')}.

            {letter_data.get('explanation', '')}

            I have a history of compliance with tax filing and payment requirements, and this was an isolated incident 
            due to the circumstances described above. I have since taken steps to ensure all future filings will be 
            timely and accurate.

            I request that the penalty be abated based on the reasonable cause explained above. If you need any additional 
            information or documentation to support this request, please contact me at [Contact Information].

            Thank you for your consideration of this matter.
            """
            for paragraph in body_text.split('\n\n'):
                elements.append(Paragraph(paragraph.strip(), normal_style))
                elements.append(Spacer(1, 12))
            
            # Closing
            elements.append(Spacer(1, 24))
            elements.append(Paragraph("Sincerely,", normal_style))
            elements.append(Spacer(1, 36))
            elements.append(Paragraph(letter_data.get("taxpayer_name", ""), normal_style))
            
        elif letter.letter_type.value == "reasonable_cause":
            # Reasonable Cause Letter
            elements.append(Paragraph("Reasonable Cause Explanation", title_style))
            elements.append(Spacer(1, 24))
            
            # Sender info
            elements.append(Paragraph(letter_data.get("taxpayer_name", ""), normal_style))
            elements.append(Paragraph(letter_data.get("taxpayer_address", ""), normal_style))
            elements.append(Paragraph(f"EIN/SSN: {letter_data.get('taxpayer_ein', '')}", normal_style))
            elements.append(Spacer(1, 24))
            
            # Date
            elements.append(Paragraph(f"Date: {letter_data.get('date', '')}", normal_style))
            elements.append(Spacer(1, 12))
            
            # Recipient - IRS
            elements.append(Paragraph("Internal Revenue Service", normal_style))
            elements.append(Paragraph("[IRS Address Placeholder]", normal_style))
            elements.append(Spacer(1, 24))
            
            # Subject
            elements.append(Paragraph(f"Subject: Reasonable Cause Explanation - Tax Year {letter_data.get('tax_year', '')}", heading_style))
            elements.append(Spacer(1, 12))
            
            # Greeting
            elements.append(Paragraph("To Whom It May Concern:", normal_style))
            elements.append(Spacer(1, 12))
            
            # Body
            body_text = f"""I am writing to explain the reasonable cause for the {letter_data.get('issue_type', '')} for 
            tax year {letter_data.get('tax_year', '')}.

            Circumstances:
            {letter_data.get('circumstances', '')}

            Resolution Steps:
            {letter_data.get('resolution', '')}

            I have taken all necessary steps to resolve this issue and ensure future compliance with all tax obligations. 
            I respectfully request that you consider these circumstances as reasonable cause and waive any associated penalties.

            If you require any additional information or documentation, please do not hesitate to contact me.
            """
            for paragraph in body_text.split('\n\n'):
                elements.append(Paragraph(paragraph.strip(), normal_style))
                elements.append(Spacer(1, 12))
            
            # Closing
            elements.append(Spacer(1, 24))
            elements.append(Paragraph("Sincerely,", normal_style))
            elements.append(Spacer(1, 36))
            elements.append(Paragraph(letter_data.get("taxpayer_name", ""), normal_style))
            
        elif letter.letter_type.value == "late_filing_relief":
            # Late Filing Relief Letter
            elements.append(Paragraph("Request for Late Filing Relief", title_style))
            elements.append(Spacer(1, 24))
            
            # Sender info
            elements.append(Paragraph(letter_data.get("taxpayer_name", ""), normal_style))
            elements.append(Paragraph(letter_data.get("taxpayer_address", ""), normal_style))
            elements.append(Paragraph(f"EIN/SSN: {letter_data.get('taxpayer_ein', '')}", normal_style))
            elements.append(Spacer(1, 24))
            
            # Date
            elements.append(Paragraph(f"Date: {letter_data.get('date', '')}", normal_style))
            elements.append(Spacer(1, 12))
            
            # Recipient - IRS
            elements.append(Paragraph("Internal Revenue Service", normal_style))
            elements.append(Paragraph("Penalty Abatement Department", normal_style))
            elements.append(Paragraph("[IRS Address Placeholder]", normal_style))
            elements.append(Spacer(1, 24))
            
            # Subject
            elements.append(Paragraph(f"Subject: Request for First-Time Penalty Abatement - Tax Year {letter_data.get('tax_year', '')}", heading_style))
            elements.append(Spacer(1, 12))
            
            # Greeting
            elements.append(Paragraph("To Whom It May Concern:", normal_style))
            elements.append(Spacer(1, 12))
            
            # Body
            body_text = f"""I am writing to request first-time penalty abatement for the late filing of my tax return for 
            the year {letter_data.get('tax_year', '')}.

            My return was due on {letter_data.get('due_date', '')} but was filed on {letter_data.get('filing_date', '')}.

            Compliance History:
            {letter_data.get('compliance_history', '')}

            Explanation for Late Filing:
            {letter_data.get('explanation', '')}

            I understand the importance of timely filing and have taken steps to ensure that all future returns will be filed 
            on time. As this is my first instance of late filing, I respectfully request that you waive the penalties under the 
            IRS First-Time Penalty Abatement policy.

            Thank you for your consideration of this request. Please contact me if you need any additional information.
            """
            for paragraph in body_text.split('\n\n'):
                elements.append(Paragraph(paragraph.strip(), normal_style))
                elements.append(Spacer(1, 12))
            
            # Closing
            elements.append(Spacer(1, 24))
            elements.append(Paragraph("Sincerely,", normal_style))
            elements.append(Spacer(1, 36))
            elements.append(Paragraph(letter_data.get("taxpayer_name", ""), normal_style))
        
        # Add disclaimer
        elements.append(Spacer(1, 36))
        disclaimer_text = "DISCLAIMER: This letter is a template provided for informational purposes only. Consult with a tax professional before submitting to the IRS. Federal Funding Club does not guarantee acceptance of penalty abatement requests."
        elements.append(Paragraph(disclaimer_text, ParagraphStyle(name='Disclaimer', fontName='Helvetica', fontSize=8, textColor=colors.red)))
        
        # Build the PDF
        doc.build(elements)
        
        return filename
    except Exception as e:
        logging.error(f"Error generating IRS letter PDF: {str(e)}")
        return None

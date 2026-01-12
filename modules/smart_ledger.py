"""
Smart Ledger Module - AI-Powered Transaction Categorization

This module provides intelligent transaction categorization using AI analysis,
automatic deduction detection, and smart tax optimization recommendations.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
import uuid

from flask import Blueprint, render_template, request, jsonify, current_app, session
from flask_login import current_user
from werkzeug.utils import secure_filename

from ai.openai_interface import get_openai_response
from app.models import User

class SmartLedger:
    """AI-powered transaction categorization and tax optimization engine"""
    
    def __init__(self):
        self.categories = {
            'business_expense': {
                'name': 'Business Expense',
                'deductible': True,
                'percentage': 100,
                'subcategories': [
                    'office_supplies', 'professional_services', 'software',
                    'equipment', 'marketing', 'travel', 'meals', 'utilities'
                ]
            },
            'office_supplies': {
                'name': 'Office Supplies',
                'deductible': True,
                'percentage': 100,
                'schedule': 'Schedule C - Line 18'
            },
            'travel': {
                'name': 'Travel Expense',
                'deductible': True,
                'percentage': 100,
                'schedule': 'Schedule C - Line 24a'
            },
            'meals': {
                'name': 'Business Meals',
                'deductible': True,
                'percentage': 50,
                'schedule': 'Schedule C - Line 24b'
            },
            'professional_services': {
                'name': 'Professional Services',
                'deductible': True,
                'percentage': 100,
                'schedule': 'Schedule C - Line 17'
            },
            'marketing': {
                'name': 'Marketing & Advertising',
                'deductible': True,
                'percentage': 100,
                'schedule': 'Schedule C - Line 8'
            },
            'equipment': {
                'name': 'Equipment Purchase',
                'deductible': True,
                'percentage': 100,
                'schedule': 'Form 4562 (Depreciation)',
                'note': 'May qualify for Section 179 deduction'
            },
            'software': {
                'name': 'Software & Subscriptions',
                'deductible': True,
                'percentage': 100,
                'schedule': 'Schedule C - Line 18'
            },
            'utilities': {
                'name': 'Utilities',
                'deductible': True,
                'percentage': 100,
                'schedule': 'Schedule C - Line 25',
                'note': 'Business portion only'
            },
            'personal': {
                'name': 'Personal Expense',
                'deductible': False,
                'percentage': 0
            }
        }
    
    def analyze_transaction(self, transaction_data: Dict) -> Dict:
        """
        Analyze a transaction using AI to determine category and deductibility
        
        Args:
            transaction_data: Dictionary containing transaction details
            
        Returns:
            Analysis results with category, confidence, and tax implications
        """
        try:
            # Prepare transaction description for AI analysis
            description = transaction_data.get('description', '')
            amount = transaction_data.get('amount', 0)
            merchant = transaction_data.get('merchant', '')
            date = transaction_data.get('date', '')
            
            # Create AI prompt for transaction categorization
            prompt = f"""
            Analyze this business transaction and categorize it for tax purposes:
            
            Merchant: {merchant}
            Description: {description}
            Amount: ${amount}
            Date: {date}
            
            Please provide:
            1. Primary category (business_expense, office_supplies, travel, meals, professional_services, marketing, equipment, software, utilities, personal)
            2. Deductibility percentage (0-100%)
            3. Confidence level (0-100%)
            4. Tax form/schedule reference
            5. Brief explanation
            6. Any special considerations or requirements
            
            Respond in JSON format.
            """
            
            # Get AI analysis
            system_msg = "You are an expert tax accountant AI assistant specialized in US tax law for freelancers and small businesses."
            ai_response = get_openai_response(system_msg, prompt, json_response=True)
            
            # Fallback if API fails or returns None
            if not ai_response:
                logging.warning("OpenAI API returned None, falling back to rule-based categorization")
                return self._rule_based_categorization(transaction_data)
            
            if ai_response:
                # Extract and validate AI response
                category = ai_response.get('category', 'personal')
                confidence = min(100, max(0, ai_response.get('confidence', 0)))
                deductible_percentage = ai_response.get('deductibility_percentage', 0)
                
                # Get category information
                category_info = self.categories.get(category, self.categories['personal'])
                
                return {
                    'category': category,
                    'category_name': category_info['name'],
                    'deductible': category_info['deductible'],
                    'deductible_percentage': deductible_percentage,
                    'confidence': confidence,
                    'schedule_reference': category_info.get('schedule', ''),
                    'explanation': ai_response.get('explanation', ''),
                    'special_notes': ai_response.get('special_considerations', ''),
                    'tax_savings_estimate': self._calculate_tax_savings(amount, deductible_percentage),
                    'ai_processed': True
                }
            else:
                # Fallback to rule-based categorization
                return self._rule_based_categorization(transaction_data)
                
        except Exception as e:
            logging.error(f"Error analyzing transaction: {str(e)}")
            return self._rule_based_categorization(transaction_data)
    
    def _rule_based_categorization(self, transaction_data: Dict) -> Dict:
        """
        Fallback rule-based categorization when AI is unavailable
        """
        description = transaction_data.get('description', '').lower()
        merchant = transaction_data.get('merchant', '').lower()
        amount = transaction_data.get('amount', 0)
        
        # Simple keyword-based categorization
        if any(keyword in description or keyword in merchant for keyword in ['office', 'supply', 'staples', 'depot']):
            category = 'office_supplies'
            confidence = 75
        elif any(keyword in description or keyword in merchant for keyword in ['travel', 'airline', 'hotel', 'uber', 'taxi']):
            category = 'travel'
            confidence = 80
        elif any(keyword in description or keyword in merchant for keyword in ['restaurant', 'cafe', 'lunch', 'dinner']):
            category = 'meals'
            confidence = 70
        elif any(keyword in description or keyword in merchant for keyword in ['software', 'subscription', 'saas', 'app']):
            category = 'software'
            confidence = 85
        else:
            category = 'business_expense'
            confidence = 50
        
        category_info = self.categories[category]
        
        return {
            'category': category,
            'category_name': category_info['name'],
            'deductible': category_info['deductible'],
            'deductible_percentage': category_info.get('percentage', 0),
            'confidence': confidence,
            'schedule_reference': category_info.get('schedule', ''),
            'explanation': f"Categorized based on merchant/description keywords",
            'special_notes': category_info.get('note', ''),
            'tax_savings_estimate': self._calculate_tax_savings(amount, category_info.get('percentage', 0)),
            'ai_processed': False
        }
    
    def _calculate_tax_savings(self, amount: float, deductible_percentage: int) -> float:
        """
        Calculate estimated tax savings for a deductible expense
        """
        # Assume average tax rate of 25% (federal + state + self-employment)
        effective_tax_rate = 0.25
        deductible_amount = amount * (deductible_percentage / 100)
        return deductible_amount * effective_tax_rate
    
    def _classify_by_keywords(self, description: str, merchant: str) -> str:
        """Classify transaction by keywords"""
        text = (description + ' ' + merchant).lower()
        
        if any(word in text for word in ['office', 'supply', 'staples', 'depot']):
            return 'office_supplies'
        elif any(word in text for word in ['travel', 'airline', 'hotel', 'uber']):
            return 'travel'
        elif any(word in text for word in ['restaurant', 'cafe', 'meal']):
            return 'meals'
        elif any(word in text for word in ['software', 'subscription', 'saas']):
            return 'software'
        elif any(word in text for word in ['marketing', 'advertising', 'ads']):
            return 'marketing'
        else:
            return 'business_expense'
    
    def process_receipt_ocr(self, file_path: str) -> Dict:
        """
        Process uploaded receipt using OCR and extract transaction data
        """
        try:
            # This would integrate with Google Vision API or similar OCR service
            # For now, return mock data
            return {
                'merchant': 'Amazon Business',
                'description': 'Office supplies - paper, pens, folders',
                'amount': 156.78,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'category_suggestions': ['office_supplies', 'business_expense']
            }
        except Exception as e:
            logging.error(f"OCR processing error: {str(e)}")
            return None
    
    def get_tax_insights(self, transactions: List[Dict]) -> Dict:
        """
        Generate comprehensive tax insights from transaction history
        """
        total_expenses = sum(t.get('amount', 0) for t in transactions if t.get('amount', 0) < 0)
        total_income = sum(t.get('amount', 0) for t in transactions if t.get('amount', 0) > 0)
        
        # Categorize transactions
        category_totals = {}
        total_deductible = 0
        total_savings = 0
        
        for transaction in transactions:
            analysis = self.analyze_transaction(transaction)
            category = analysis['category']
            amount = abs(transaction.get('amount', 0))
            
            if category not in category_totals:
                category_totals[category] = 0
            category_totals[category] += amount
            
            if analysis['deductible']:
                deductible_amount = amount * (analysis['deductible_percentage'] / 100)
                total_deductible += deductible_amount
                total_savings += analysis['tax_savings_estimate']
        
        # Generate insights
        insights = {
            'summary': {
                'total_expenses': abs(total_expenses),
                'total_income': total_income,
                'total_deductible': total_deductible,
                'estimated_tax_savings': total_savings,
                'average_confidence': 89  # Mock confidence score
            },
            'category_breakdown': category_totals,
            'recommendations': [
                {
                    'type': 'deduction_opportunity',
                    'title': 'Home Office Deduction',
                    'description': 'You may qualify for home office deduction if you use part of your home exclusively for business.',
                    'potential_savings': 340,
                    'action': 'Track home office usage and expenses'
                },
                {
                    'type': 'missing_documentation',
                    'title': 'Missing Receipts',
                    'description': 'Some expenses lack proper documentation for audit protection.',
                    'potential_risk': 89,
                    'action': 'Upload receipts for undocumented expenses'
                },
                {
                    'type': 'optimization',
                    'title': 'Meal Deduction Optimization',
                    'description': 'Business meals are 50% deductible. Ensure proper documentation.',
                    'potential_savings': 120,
                    'action': 'Document business purpose for meal expenses'
                }
            ],
            'upcoming_deadlines': [
                {
                    'date': '2025-01-15',
                    'description': 'Q4 2024 estimated tax payments due',
                    'type': 'payment'
                },
                {
                    'date': '2025-03-15',
                    'description': 'File 2024 tax return (with extension)',
                    'type': 'filing'
                }
            ]
        }
        
        return insights

# Flask Blueprint for Smart Ledger routes
smart_ledger_bp = Blueprint('smart_ledger', __name__)

@smart_ledger_bp.route('/smart-ledger')
def smart_ledger():
    """Smart Ledger main page"""
    return render_template('smart_ledger.html')

@smart_ledger_bp.route('/api/analyze-transaction', methods=['POST'])
def analyze_transaction():
    """API endpoint for transaction analysis with subscription check"""
    try:
        # CHECK FOR SMART LEDGER SUBSCRIPTION
        if not current_user or not current_user.is_authenticated:
            return jsonify({
                'error': 'AUTHENTICATION_REQUIRED',
                'message': 'Please log in to use Smart Ledger AI'
            }), 401

        if not current_user.has_feature('smart_ledger_ai'):
            return jsonify({
                'error': 'UPGRADE_REQUIRED',
                'message': 'AI expense categorization requires Smart Ledger add-on',
                'pricing': {
                    'monthly': 12.97,
                    'annual': 147,
                    'features': [
                        'AI-powered transaction categorization',
                        'Tax-readiness score',
                        'Automatic deduction finder',
                        'Real-time expense tracking'
                    ]
                },
                'upgrade_url': '/pricing#smart-ledger'
            }), 403

        # User has access - proceed with AI categorization
        ledger = SmartLedger()
        transaction_data = request.get_json()

        if not transaction_data:
            return jsonify({'error': 'No transaction data provided'}), 400

        analysis = ledger.analyze_transaction(transaction_data)
        return jsonify(analysis)

    except Exception as e:
        logging.error(f"Transaction analysis error: {str(e)}")
        return jsonify({'error': 'Analysis failed'}), 500

@smart_ledger_bp.route('/api/upload-receipt', methods=['POST'])
def upload_receipt():
    """API endpoint for receipt upload and OCR processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        file_path = os.path.join('uploads', f"{file_id}_{filename}")
        
        # Ensure uploads directory exists
        os.makedirs('uploads', exist_ok=True)
        file.save(file_path)
        
        # Process with OCR
        ledger = SmartLedger()
        ocr_result = ledger.process_receipt_ocr(file_path)
        
        if ocr_result:
            # Analyze the extracted transaction
            analysis = ledger.analyze_transaction(ocr_result)
            
            return jsonify({
                'success': True,
                'file_id': file_id,
                'extracted_data': ocr_result,
                'analysis': analysis
            })
        else:
            return jsonify({'error': 'OCR processing failed'}), 500
            
    except Exception as e:
        logging.error(f"Receipt upload error: {str(e)}")
        return jsonify({'error': 'Upload failed'}), 500

@smart_ledger_bp.route('/api/tax-insights')
def get_tax_insights():
    """API endpoint for tax insights generation"""
    try:
        # Mock transaction data for demo
        mock_transactions = [
            {'merchant': 'Office Depot', 'description': 'Office supplies', 'amount': -89.47, 'date': '2024-12-15'},
            {'merchant': 'Delta Airlines', 'description': 'Business travel', 'amount': -432.89, 'date': '2024-12-12'},
            {'merchant': 'ABC Corp', 'description': 'Client payment', 'amount': 2500.00, 'date': '2024-12-10'},
            {'merchant': 'Starbucks', 'description': 'Business meeting', 'amount': -25.50, 'date': '2024-12-08'},
            {'merchant': 'Amazon Business', 'description': 'Office equipment', 'amount': -156.78, 'date': '2024-12-05'}
        ]
        
        ledger = SmartLedger()
        insights = ledger.get_tax_insights(mock_transactions)
        
        return jsonify(insights)
        
    except Exception as e:
        logging.error(f"Tax insights error: {str(e)}")
        return jsonify({'error': 'Failed to generate insights'}), 500

def init_smart_ledger(app):
    """Initialize Smart Ledger module with Flask app"""
    app.register_blueprint(smart_ledger_bp, url_prefix='/ledger')
    logging.info("Smart Ledger module initialized")
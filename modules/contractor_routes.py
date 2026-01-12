"""
Contractor Management Routes - 1099 Management with Business Credit Reporting

This module handles contractor management, payment tracking, and 1099-NEC form generation.
Premium feature that helps build business credit through Net-30 reporting.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import func

from app import db
from app.models import Contractor, ContractorPayment, Form1099, User
from app.access_control import requires_access_level
from modules.pdf_utils import generate_tax_form_pdf

# Create blueprint
contractor_bp = Blueprint('contractors', __name__, url_prefix='/contractors')


@contractor_bp.route('/dashboard')
@login_required
def dashboard():
    """Contractor management dashboard with subscription gate"""
    # Check if user has contractor management access
    has_access = (
        current_user.has_feature('contractor_management') or
        current_user.has_feature('contractor_management_addon')
    )

    if not has_access:
        # Show upgrade prompt
        return render_template('contractors/dashboard.html',
                             contractors=[],
                             needs_upgrade=True,
                             total_contractors=0,
                             contractors_need_1099=0,
                             total_paid_ytd=0)

    # User has access - show full dashboard
    contractors = Contractor.query.filter_by(user_id=current_user.id).all()

    # Calculate summary stats
    total_paid_ytd = db.session.query(
        func.sum(Contractor.total_paid_ytd)
    ).filter(
        Contractor.user_id == current_user.id
    ).scalar() or 0

    contractors_need_1099 = Contractor.query.filter_by(
        user_id=current_user.id,
        needs_1099=True
    ).count()

    return render_template('contractors/dashboard.html',
                         contractors=contractors,
                         needs_upgrade=False,
                         total_contractors=len(contractors),
                         contractors_need_1099=contractors_need_1099,
                         total_paid_ytd=total_paid_ytd)


@contractor_bp.route('/add', methods=['GET', 'POST'])
@login_required
@requires_access_level('contractor_management')
def add_contractor():
    """Add new contractor"""
    if request.method == 'POST':
        try:
            data = request.form

            contractor = Contractor(
                user_id=current_user.id,
                name=data.get('name'),
                business_name=data.get('business_name'),
                email=data.get('email'),
                phone=data.get('phone'),
                ein=data.get('ein'),
                address_line1=data.get('address_line1'),
                address_line2=data.get('address_line2'),
                city=data.get('city'),
                state=data.get('state'),
                zip_code=data.get('zip_code'),
                total_paid_ytd=0,
                needs_1099=False
            )

            db.session.add(contractor)
            db.session.commit()

            flash(f'Contractor {contractor.name} added successfully!', 'success')
            return redirect(url_for('contractors.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding contractor: {str(e)}', 'danger')
            return redirect(url_for('contractors.add_contractor'))

    return render_template('contractors/add_contractor.html')


@contractor_bp.route('/payment/add', methods=['POST'])
@login_required
@requires_access_level('contractor_management')
def add_payment():
    """Add payment to contractor"""
    try:
        data = request.get_json() if request.is_json else request.form

        contractor_id = data.get('contractor_id')
        amount = Decimal(str(data.get('amount', 0)))
        payment_date_str = data.get('payment_date')

        # Parse payment date
        if isinstance(payment_date_str, str):
            payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
        else:
            payment_date = date.today()

        # Get contractor
        contractor = Contractor.query.filter_by(
            id=contractor_id,
            user_id=current_user.id
        ).first_or_404()

        # Create payment record
        payment = ContractorPayment(
            contractor_id=contractor.id,
            user_id=current_user.id,
            amount=amount,
            payment_date=payment_date,
            description=data.get('description', ''),
            category=data.get('category', 'Services')
        )

        db.session.add(payment)

        # Update contractor's total_paid_ytd
        contractor.total_paid_ytd = (contractor.total_paid_ytd or 0) + amount

        # Check if contractor needs 1099 (>$600)
        if contractor.total_paid_ytd >= 600:
            contractor.needs_1099 = True

        db.session.commit()

        if request.is_json:
            return jsonify({
                'success': True,
                'message': f'Payment of ${amount} recorded',
                'contractor': {
                    'id': contractor.id,
                    'name': contractor.name,
                    'total_paid_ytd': float(contractor.total_paid_ytd),
                    'needs_1099': contractor.needs_1099
                }
            })
        else:
            flash(f'Payment of ${amount} recorded for {contractor.name}', 'success')
            return redirect(url_for('contractors.dashboard'))

    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        else:
            flash(f'Error recording payment: {str(e)}', 'danger')
            return redirect(url_for('contractors.dashboard'))


@contractor_bp.route('/1099/generate/<int:contractor_id>')
@login_required
@requires_access_level('contractor_management')
def generate_1099(contractor_id):
    """Generate 1099-NEC form for contractor"""
    try:
        contractor = Contractor.query.filter_by(
            id=contractor_id,
            user_id=current_user.id
        ).first_or_404()

        # Check if contractor needs 1099
        if not contractor.needs_1099:
            flash(f'{contractor.name} has not reached $600 threshold for 1099', 'warning')
            return redirect(url_for('contractors.dashboard'))

        # Get current tax year
        current_year = datetime.now().year
        tax_year = current_year - 1  # Previous year

        # Check if 1099 already exists
        existing_1099 = Form1099.query.filter_by(
            user_id=current_user.id,
            contractor_id=contractor.id,
            tax_year=tax_year
        ).first()

        if existing_1099:
            flash(f'1099 for {contractor.name} ({tax_year}) already exists', 'info')
            return redirect(url_for('contractors.dashboard'))

        # Create 1099 form
        form_1099 = Form1099(
            user_id=current_user.id,
            contractor_id=contractor.id,
            tax_year=tax_year,
            total_amount=contractor.total_paid_ytd,
            form_data={
                'payer_name': current_user.username,
                'payer_ein': 'TO_BE_FILLED',
                'recipient_name': contractor.name,
                'recipient_ein': contractor.ein,
                'recipient_address': f"{contractor.address_line1}, {contractor.city}, {contractor.state} {contractor.zip_code}",
                'nonemployee_compensation': float(contractor.total_paid_ytd),
                'federal_tax_withheld': 0,
                'state_tax_withheld': 0
            },
            status='draft'
        )

        db.session.add(form_1099)
        db.session.commit()
        
        # Generate PDF
        pdf_filename = generate_tax_form_pdf(form_1099)
        
        if pdf_filename:
            # Store PDF filename in form_data
            # Re-assigning to trigger SQLAlchemy update for JSON field
            form_data = dict(form_1099.form_data)
            form_data['pdf_file'] = pdf_filename
            form_1099.form_data = form_data
            db.session.commit()
            
            flash(f'1099-NEC generated for {contractor.name} (Tax Year {tax_year}). API File: {pdf_filename}', 'success')
        else:
            flash(f'1099-NEC generated for {contractor.name} (Tax Year {tax_year}), but PDF generation failed.', 'warning')
            
        return redirect(url_for('contractors.dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error generating 1099: {str(e)}', 'danger')
        return redirect(url_for('contractors.dashboard'))


@contractor_bp.route('/api/summary')
@login_required
def api_summary():
    """API endpoint for contractor summary stats"""
    try:
        # Check access
        has_access = (
            current_user.has_feature('contractor_management') or
            current_user.has_feature('contractor_management_addon')
        )

        if not has_access:
            return jsonify({
                'error': 'UPGRADE_REQUIRED',
                'message': 'Contractor management requires upgrade',
                'pricing': {
                    'addon_monthly': 19,
                    'premium_annual': 497
                }
            }), 403

        # Calculate summary
        total_contractors = Contractor.query.filter_by(user_id=current_user.id).count()

        contractors_need_1099 = Contractor.query.filter_by(
            user_id=current_user.id,
            needs_1099=True
        ).count()

        total_paid = db.session.query(
            func.sum(Contractor.total_paid_ytd)
        ).filter(
            Contractor.user_id == current_user.id
        ).scalar() or 0

        return jsonify({
            'success': True,
            'total_contractors': total_contractors,
            'contractors_need_1099': contractors_need_1099,
            'total_paid_ytd': float(total_paid)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@contractor_bp.route('/delete/<int:contractor_id>', methods=['POST'])
@login_required
@requires_access_level('contractor_management')
def delete_contractor(contractor_id):
    """Delete contractor"""
    try:
        contractor = Contractor.query.filter_by(
            id=contractor_id,
            user_id=current_user.id
        ).first_or_404()

        contractor_name = contractor.name

        # Delete associated payments
        ContractorPayment.query.filter_by(contractor_id=contractor.id).delete()

        # Delete associated 1099 forms
        Form1099.query.filter_by(contractor_id=contractor.id).delete()

        # Delete contractor
        db.session.delete(contractor)
        db.session.commit()

        flash(f'Contractor {contractor_name} deleted successfully', 'success')
        return redirect(url_for('contractors.dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting contractor: {str(e)}', 'danger')
        return redirect(url_for('contractors.dashboard'))

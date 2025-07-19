import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from app import db
from models.promotion import SocialPromotion, SocialPlatform, PromotionType, PromotionSettings
from models.user import User
from utils.helpers import admin_required
import uuid

promotions_bp = Blueprint('promotions', __name__)

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'payment_proofs')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@promotions_bp.route('/promotions')
@login_required
def promotions_dashboard():
    """User promotions dashboard"""
    user_promotions = SocialPromotion.query.filter_by(user_id=current_user.id).order_by(SocialPromotion.created_at.desc()).all()
    platforms = SocialPlatform.query.filter_by(is_active=True).all()
    promo_types = PromotionType.query.filter_by(is_active=True).all()
    settings = PromotionSettings.get_settings()
    
    return render_template('promotions/dashboard.html', 
                         promotions=user_promotions,
                         platforms=platforms,
                         promo_types=promo_types,
                         settings=settings)

@promotions_bp.route('/promotions/create', methods=['GET', 'POST'])
@login_required
def create_promotion():
    """Create new promotion campaign"""
    if request.method == 'GET':
        platforms = SocialPlatform.query.filter_by(is_active=True).all()
        promo_types = PromotionType.query.filter_by(is_active=True).all()
        settings = PromotionSettings.get_settings()
        return render_template('promotions/create.html', 
                             platforms=platforms,
                             promo_types=promo_types,
                             settings=settings)
    
    # Process form submission
    try:
        # Validate CSRF token
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(request.form.get('csrf_token'))
        except Exception:
            flash('Security token invalid. Please try again.', 'error')
            return redirect(url_for('promotions.create_promotion'))
        
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        social_url = request.form.get('social_url', '').strip()
        platform_id = request.form.get('platform_id', type=int)
        promotion_type_id = request.form.get('promotion_type_id', type=int)
        budget = request.form.get('budget', type=float)
        
        # Validation
        if not all([title, social_url, platform_id, promotion_type_id, budget]):
            flash('All fields are required.', 'error')
            return redirect(url_for('promotions.create_promotion'))
        
        settings = PromotionSettings.get_settings()
        if budget < settings.min_budget or budget > settings.max_budget:
            flash(f'Budget must be between ${settings.min_budget} and ${settings.max_budget}.', 'error')
            return redirect(url_for('promotions.create_promotion'))
        
        # Verify platform and promotion type exist
        platform = SocialPlatform.query.get(platform_id)
        promo_type = PromotionType.query.get(promotion_type_id)
        if not platform or not promo_type:
            flash('Invalid platform or promotion type.', 'error')
            return redirect(url_for('promotions.create_promotion'))
        
        # Create promotion
        promotion = SocialPromotion(
            title=title,
            description=description,
            social_url=social_url,
            user_id=current_user.id,
            platform_id=platform_id,
            promotion_type_id=promotion_type_id,
            budget=budget
        )
        
        # Auto-approve small campaigns if enabled
        if budget <= settings.auto_approve_under and not settings.require_manual_review:
            promotion.is_approved = True
            promotion.approved_at = datetime.utcnow()
        
        db.session.add(promotion)
        db.session.commit()
        
        flash(f'Promotion campaign created! Invoice #{promotion.invoice_number}', 'success')
        return redirect(url_for('promotions.view_promotion', promotion_id=promotion.id))
        
    except Exception as e:
        db.session.rollback()
        flash('Error creating promotion campaign.', 'error')
        return redirect(url_for('promotions.create_promotion'))

@promotions_bp.route('/promotions/<int:promotion_id>')
@login_required
def view_promotion(promotion_id):
    """View promotion details and invoice"""
    promotion = SocialPromotion.query.get_or_404(promotion_id)
    
    # Check permission
    if promotion.user_id != current_user.id and not current_user.is_admin:
        flash('Permission denied.', 'error')
        return redirect(url_for('promotions.promotions_dashboard'))
    
    settings = PromotionSettings.get_settings()
    return render_template('promotions/view.html', promotion=promotion, settings=settings)

@promotions_bp.route('/promotions/<int:promotion_id>/upload-payment', methods=['POST'])
@login_required
def upload_payment_proof(promotion_id):
    """Upload payment proof"""
    promotion = SocialPromotion.query.get_or_404(promotion_id)
    
    # Check permission
    if promotion.user_id != current_user.id:
        flash('Permission denied.', 'error')
        return redirect(url_for('promotions.promotions_dashboard'))
    
    if 'payment_proof' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('promotions.view_promotion', promotion_id=promotion_id))
    
    file = request.files['payment_proof']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('promotions.view_promotion', promotion_id=promotion_id))
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = f"{promotion.invoice_number}_{secure_filename(file.filename)}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Update promotion
        promotion.payment_proof = filename
        promotion.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Payment proof uploaded successfully! Admin will review and confirm payment.', 'success')
    else:
        flash('Invalid file type. Please upload PNG, JPG, JPEG, GIF, or PDF files only.', 'error')
    
    return redirect(url_for('promotions.view_promotion', promotion_id=promotion_id))

@promotions_bp.route('/promotions/<int:promotion_id>/invoice')
@login_required
def download_invoice(promotion_id):
    """Download invoice as PDF (simplified HTML for now)"""
    promotion = SocialPromotion.query.get_or_404(promotion_id)
    
    # Check permission
    if promotion.user_id != current_user.id and not current_user.is_admin:
        flash('Permission denied.', 'error')
        return redirect(url_for('promotions.promotions_dashboard'))
    
    settings = PromotionSettings.get_settings()
    return render_template('promotions/invoice.html', promotion=promotion, settings=settings)

@promotions_bp.route('/admin/promotions')
@login_required
@admin_required
def admin_promotions():
    """Admin promotions management"""
    status_filter = request.args.get('status', 'all')
    
    query = SocialPromotion.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    promotions = query.order_by(SocialPromotion.created_at.desc()).all()
    
    # Statistics
    stats = {
        'total': SocialPromotion.query.count(),
        'pending': SocialPromotion.query.filter_by(status='pending').count(),
        'active': SocialPromotion.query.filter_by(status='active').count(),
        'completed': SocialPromotion.query.filter_by(status='completed').count(),
        'pending_payment': SocialPromotion.query.filter_by(is_paid=False).count(),
        'total_revenue': db.session.query(db.func.sum(SocialPromotion.budget)).filter_by(is_paid=True).scalar() or 0
    }
    
    return render_template('admin/promotions.html', promotions=promotions, stats=stats, status_filter=status_filter)

@promotions_bp.route('/admin/promotions/<int:promotion_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_promotion(promotion_id):
    """Approve promotion campaign"""
    promotion = SocialPromotion.query.get_or_404(promotion_id)
    
    promotion.is_approved = True
    promotion.approved_at = datetime.utcnow()
    promotion.admin_notes = request.form.get('admin_notes', '')
    
    # Start campaign if already paid
    if promotion.is_paid:
        promotion.start_campaign()
    
    db.session.commit()
    flash('Promotion approved successfully!', 'success')
    return redirect(url_for('promotions.admin_promotions'))

@promotions_bp.route('/admin/promotions/<int:promotion_id>/mark-paid', methods=['POST'])
@login_required
@admin_required
def mark_promotion_paid(promotion_id):
    """Mark promotion as paid"""
    promotion = SocialPromotion.query.get_or_404(promotion_id)
    
    promotion.mark_as_paid()
    promotion.admin_notes = request.form.get('admin_notes', '')
    
    # Start campaign if already approved
    if promotion.is_approved:
        promotion.start_campaign()
    
    db.session.commit()
    flash('Promotion marked as paid!', 'success')
    return redirect(url_for('promotions.admin_promotions'))

@promotions_bp.route('/admin/promotions/<int:promotion_id>/start', methods=['POST'])
@login_required
@admin_required
def start_promotion(promotion_id):
    """Start promotion campaign"""
    promotion = SocialPromotion.query.get_or_404(promotion_id)
    
    if not promotion.is_approved:
        flash('Promotion must be approved first.', 'error')
        return redirect(url_for('promotions.admin_promotions'))
    
    if not promotion.is_paid:
        flash('Payment must be confirmed first.', 'error')
        return redirect(url_for('promotions.admin_promotions'))
    
    promotion.start_campaign()
    db.session.commit()
    
    flash('Promotion campaign started!', 'success')
    return redirect(url_for('promotions.admin_promotions'))

@promotions_bp.route('/admin/promotion-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def promotion_settings():
    """Manage promotion system settings"""
    settings = PromotionSettings.get_settings()
    
    if request.method == 'POST':
        try:
            # Update settings
            settings.payment_instructions = request.form.get('payment_instructions', '')
            settings.daily_rate = float(request.form.get('daily_rate', 5.0))
            settings.min_budget = float(request.form.get('min_budget', 5.0))
            settings.max_budget = float(request.form.get('max_budget', 1000.0))
            settings.business_name = request.form.get('business_name', '')
            settings.business_address = request.form.get('business_address', '')
            settings.business_email = request.form.get('business_email', '')
            settings.business_phone = request.form.get('business_phone', '')
            settings.tax_id = request.form.get('tax_id', '')
            settings.auto_approve_under = float(request.form.get('auto_approve_under', 50.0))
            settings.require_manual_review = 'require_manual_review' in request.form
            settings.terms_and_conditions = request.form.get('terms_and_conditions', '')
            settings.updated_by = current_user.id
            settings.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Promotion settings updated successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('Error updating settings.', 'error')
    
    # Get platforms and promotion types for management
    platforms = SocialPlatform.query.all()
    promo_types = PromotionType.query.all()
    
    return render_template('admin/promotion_settings.html', 
                         settings=settings, 
                         platforms=platforms, 
                         promo_types=promo_types)

@promotions_bp.route('/uploads/payment_proofs/<filename>')
@login_required
def uploaded_payment_proof(filename):
    """Serve payment proof files (admin only)"""
    if not current_user.is_admin:
        flash('Permission denied.', 'error')
        return redirect(url_for('index'))
    
    return send_from_directory(UPLOAD_FOLDER, filename)
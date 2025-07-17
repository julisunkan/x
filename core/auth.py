from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
import os
import uuid
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from app import db
from models.user import User
from models.referral import Referral, ReferralSettings
from models.settings import AppSettings
from forms import LoginForm, RegisterForm, ProfileUpdateForm, ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm
from utils.helpers import generate_referral_code, send_email
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Maintenance mode check is handled after authentication to allow admin access
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html', form=form)
            
            if not user.email_verified:
                flash('Please verify your email address before logging in. Check your inbox for the verification link.', 'warning')
                return render_template('auth/login.html', form=form)
            
            # Check maintenance mode for non-admin users
            try:
                settings = AppSettings.get_settings()
                if settings.maintenance_mode and not user.is_admin:
                    flash('The platform is currently under maintenance. Only administrators can access the system.', 'error')
                    return render_template('auth/login.html', form=form)
            except Exception as e:
                logging.error(f"Error checking maintenance mode for user: {str(e)}")
            
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            logging.info(f"User {username} logged in successfully")
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Check maintenance mode - block all registrations
    try:
        settings = AppSettings.get_settings()
        if settings.maintenance_mode:
            maintenance_message = settings.maintenance_message or "The platform is currently under maintenance. Please try again later."
            return render_template('maintenance.html', message=maintenance_message), 503
    except Exception as e:
        logging.error(f"Error checking maintenance mode in register: {str(e)}")
    
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        confirm_password = form.confirm_password.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        referral_code = form.referral_code.data
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('auth/register.html', form=form)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html', form=form)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('auth/register.html', form=form)
        
        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            form.username.errors.append('Username already exists.')
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            form.email.errors.append('Email already registered.')
        
        # Handle profile image upload
        profile_image_filename = None
        if form.profile_image.data:
            file = form.profile_image.data
            if file.filename:
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join(os.getcwd(), 'static', 'uploads', 'profiles')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Generate unique filename
                filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
                filepath = os.path.join(upload_dir, filename)
                
                try:
                    file.save(filepath)
                    profile_image_filename = filename
                except Exception as e:
                    logging.error(f"Profile image upload error: {str(e)}")
                    form.profile_image.errors.append('Failed to upload profile image.')
        
        # If there are validation errors, return to form
        if form.username.errors or form.email.errors or form.profile_image.errors:
            return render_template('auth/register.html', form=form)
        
        # Handle referral
        referrer = None
        if referral_code:
            referrer = User.query.filter_by(referral_code=referral_code).first()
            if not referrer:
                flash('Invalid referral code.', 'warning')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            balance=100.0,  # Welcome bonus
            referred_by=referrer.id if referrer else None,
            profile_image=profile_image_filename,
            email_verified=False
        )
        
        # Generate email verification token
        user.email_verification_token = user.generate_verification_token()
        user.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Create referral relationship
            if referrer:
                referral = Referral(
                    referrer_id=referrer.id,
                    referred_id=user.id,
                    referral_code=referral_code
                )
                db.session.add(referral)
                
                # Give referrer signup bonus
                settings = ReferralSettings.get_settings()
                referrer.balance += settings.signup_bonus
                referral.earnings += settings.signup_bonus
                
                db.session.commit()
                
                logging.info(f"New user {username} registered with referral from {referrer.username}")
            else:
                logging.info(f"New user {username} registered without referral")
            
            # Send verification email
            verification_link = url_for('auth.verify_email', token=user.email_verification_token, _external=True)
            email_body = f"""
            Welcome to RoseCoin!
            
            Please verify your email address by clicking the link below:
            {verification_link}
            
            This link will expire in 24 hours.
            
            If you didn't create this account, please ignore this email.
            """
            
            send_email(email, 'Verify Your RoseCoin Account', email_body)
            
            flash('Registration successful! Please check your email to verify your account before logging in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logging.info(f"User {current_user.username} logged out")
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    
    # Check if email is already taken by another user
    if email != current_user.email:
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered to another account.', 'error')
            return redirect(url_for('profile'))
    
    current_user.first_name = first_name
    current_user.last_name = last_name
    current_user.email = email
    
    # Handle profile image upload
    if 'profile_image' in request.files:
        file = request.files['profile_image']
        if file and file.filename:
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join(os.getcwd(), 'static', 'uploads', 'profiles')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            import uuid
            filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
            filepath = os.path.join(upload_dir, filename)
            
            # Delete old profile image if exists
            if current_user.profile_image:
                old_filepath = os.path.join(upload_dir, current_user.profile_image)
                if os.path.exists(old_filepath):
                    os.remove(old_filepath)
            
            # Save new image
            file.save(filepath)
            current_user.profile_image = filename
    
    try:
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Profile update error: {str(e)}")
        flash('An error occurred while updating your profile.', 'error')
    
    return redirect(url_for('profile'))

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('profile'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters long.', 'error')
        return redirect(url_for('profile'))
    
    current_user.password_hash = generate_password_hash(new_password)
    
    try:
        db.session.commit()
        flash('Password changed successfully!', 'success')
        logging.info(f"User {current_user.username} changed password")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Password change error: {str(e)}")
        flash('An error occurred while changing your password.', 'error')
    
    return redirect(url_for('profile'))

@auth_bp.route('/update_wallet', methods=['POST'])
@login_required
def update_wallet():
    wallet_type = request.form.get('wallet_type')
    wallet_address = request.form.get('wallet_address')
    
    if wallet_type and wallet_address:
        current_user.wallet_type = wallet_type
        current_user.wallet_address = wallet_address
        db.session.commit()
        flash('Wallet settings updated successfully!', 'success')
    else:
        flash('Please provide both wallet type and address.', 'error')
    
    return redirect(url_for('profile'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = user.generate_password_reset_token()
            user.password_reset_token = token
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
            
            try:
                db.session.commit()
                
                # Send email with reset link
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                send_password_reset_email(user.email, reset_url)
                
                flash('If that email address is in our system, you will receive a password reset link shortly.', 'info')
                logging.info(f"Password reset requested for user: {user.username}")
                
            except Exception as e:
                db.session.rollback()
                logging.error(f"Password reset error: {str(e)}")
                flash('An error occurred. Please try again.', 'error')
        else:
            # Don't reveal if email exists or not
            flash('If that email address is in our system, you will receive a password reset link shortly.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    user = User.query.filter_by(password_reset_token=token).first()
    
    if not user or not user.is_password_reset_token_valid(token):
        flash('Invalid or expired reset link. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password_hash = generate_password_hash(form.password.data)
        user.password_reset_token = None
        user.password_reset_expires = None
        
        try:
            db.session.commit()
            flash('Your password has been reset successfully! You can now log in.', 'success')
            logging.info(f"Password reset successful for user: {user.username}")
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Password reset completion error: {str(e)}")
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('auth/reset_password.html', form=form)

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(email_verification_token=token).first()
    
    if not user:
        return render_template('auth/verify_email.html', verification_status='invalid')
    
    if not user.is_verification_token_valid(token):
        return render_template('auth/verify_email.html', verification_status='expired')
    
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    
    try:
        db.session.commit()
        flash('Your email has been verified successfully!', 'success')
        logging.info(f"Email verified for user: {user.username}")
        return render_template('auth/verify_email.html', verification_status='success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Email verification error: {str(e)}")
        flash('An error occurred during verification.', 'error')
        return render_template('auth/verify_email.html', verification_status='invalid')

@auth_bp.route('/resend-verification')
def resend_verification():
    if current_user.is_authenticated:
        if current_user.email_verified:
            flash('Your email is already verified.', 'info')
            return redirect(url_for('dashboard'))
        
        # Generate new verification token
        token = current_user.generate_verification_token()
        current_user.email_verification_token = token
        current_user.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        try:
            db.session.commit()
            
            # Send verification email
            verify_url = url_for('auth.verify_email', token=token, _external=True)
            send_verification_email(current_user.email, verify_url)
            
            flash('A new verification email has been sent to your email address.', 'info')
            logging.info(f"Verification email resent for user: {current_user.username}")
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Resend verification error: {str(e)}")
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('auth/verify_email.html')

def send_password_reset_email(email, reset_url):
    """Send password reset email using SendGrid"""
    try:
        # Import SendGrid if available
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logging.warning("SendGrid API key not found. Email not sent.")
            return False
        
        sg = SendGridAPIClient(api_key)
        
        html_content = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested a password reset for your RoseCoin account.</p>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this reset, please ignore this email.</p>
        </body>
        </html>
        """
        
        message = Mail(
            from_email='noreply@rosecoin.app',
            to_emails=email,
            subject='Password Reset - RoseCoin',
            html_content=html_content
        )
        
        response = sg.send(message)
        return response.status_code == 202
        
    except Exception as e:
        logging.error(f"Failed to send password reset email: {str(e)}")
        return False

def send_verification_email(email, verify_url):
    """Send email verification email using SendGrid"""
    try:
        # Import SendGrid if available
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logging.warning("SendGrid API key not found. Email not sent.")
            return False
        
        sg = SendGridAPIClient(api_key)
        
        html_content = f"""
        <html>
        <body>
            <h2>Email Verification - RoseCoin</h2>
            <p>Thank you for signing up for RoseCoin!</p>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verify_url}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create this account, please ignore this email.</p>
        </body>
        </html>
        """
        
        message = Mail(
            from_email='noreply@rosecoin.app',
            to_emails=email,
            subject='Email Verification - RoseCoin',
            html_content=html_content
        )
        
        response = sg.send(message)
        return response.status_code == 202
        
    except Exception as e:
        logging.error(f"Failed to send verification email: {str(e)}")
        return False



import os
import uuid
import random
import string
from flask import request
from werkzeug.utils import secure_filename
from datetime import datetime

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = 'uploads'

def get_client_ip():
    """Get the real IP address of the client"""
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, subfolder='general'):
    """Save uploaded file and return the file path"""
    if file and allowed_file(file.filename):
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(UPLOAD_FOLDER, subfolder)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Return relative path from uploads directory (without 'uploads/' prefix)
        return os.path.join(subfolder, unique_filename)
    return None

def generate_referral_code(length=8):
    """Generate a random referral code"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))

def format_coins(amount):
    """Format coin amount for display"""
    if amount >= 1000000:
        return f"{amount/1000000:.2f}M"
    elif amount >= 1000:
        return f"{amount/1000:.2f}K"
    else:
        return f"{amount:.4f}"

def calculate_level_from_xp(xp):
    """Calculate user level based on XP"""
    return max(1, int(xp / 1000) + 1)

def calculate_xp_for_level(level):
    """Calculate XP required for a specific level"""
    return (level - 1) * 1000

def time_until_next_mining():
    """Calculate time until user can mine again (if there's a cooldown)"""
    # This could be expanded to implement actual cooldown logic
    return 0

def is_valid_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_input(text):
    """Basic input sanitization"""
    if not text:
        return ""
    # Remove potentially dangerous characters
    return text.strip()[:500]  # Limit length and trim

def generate_avatar_url(seed):
    """Generate avatar URL using Pravatar API"""
    return f"https://api.pravatar.cc/150?u={seed}"

def calculate_mining_power(level, base_power=1.0):
    """Calculate mining power based on user level"""
    return base_power + (level - 1) * 0.1

def get_user_stats_summary(user):
    """Get a summary of user statistics"""
    from models.mining import MiningSession
    from models.task import TaskCompletion
    from models.referral import Referral
    from app import db
    from sqlalchemy import func
    
    total_mined = db.session.query(func.sum(MiningSession.coins_earned)).filter_by(user_id=user.id).scalar() or 0
    completed_tasks = TaskCompletion.query.filter_by(user_id=user.id, status='approved').count()
    referral_count = Referral.query.filter_by(referrer_id=user.id).count()
    
    return {
        'total_mined': total_mined,
        'completed_tasks': completed_tasks,
        'referral_count': referral_count,
        'level': user.level,
        'xp': user.xp,
        'balance': user.balance
    }

def validate_withdrawal_amount(amount, user_balance, settings):
    """Validate withdrawal request"""
    errors = []
    
    if amount <= 0:
        errors.append("Amount must be greater than 0")
    
    if amount < settings.min_withdrawal_amount:
        errors.append(f"Minimum withdrawal amount is {settings.min_withdrawal_amount}")
    
    if amount > settings.max_withdrawal_amount:
        errors.append(f"Maximum withdrawal amount is {settings.max_withdrawal_amount}")
    
    if amount > user_balance:
        errors.append("Insufficient balance")
    
    return errors

def log_user_activity(user, activity_type, details=""):
    """Log user activity for audit purposes"""
    import logging
    logging.info(f"User {user.username} (ID: {user.id}): {activity_type} - {details}")

def get_platform_icon(platform):
    """Get Font Awesome icon class for social media platforms"""
    platform_icons = {
        'twitter': 'fab fa-twitter',
        'telegram': 'fab fa-telegram',
        'youtube': 'fab fa-youtube',
        'instagram': 'fab fa-instagram',
        'facebook': 'fab fa-facebook',
        'discord': 'fab fa-discord',
        'tiktok': 'fab fa-tiktok',
        'linkedin': 'fab fa-linkedin'
    }
    return platform_icons.get(platform.lower(), 'fas fa-link')

def get_task_type_icon(task_type):
    """Get Font Awesome icon class for task types"""
    task_icons = {
        'like': 'fas fa-heart',
        'follow': 'fas fa-user-plus',
        'share': 'fas fa-share',
        'subscribe': 'fas fa-bell',
        'comment': 'fas fa-comment',
        'join': 'fas fa-users',
        'visit': 'fas fa-external-link-alt'
    }
    return task_icons.get(task_type.lower(), 'fas fa-tasks')

def get_status_badge_class(status):
    """Get Bootstrap badge class for different statuses"""
    status_classes = {
        'pending': 'badge-warning',
        'approved': 'badge-success',
        'rejected': 'badge-danger',
        'paid': 'badge-success',
        'active': 'badge-success',
        'inactive': 'badge-secondary'
    }
    return status_classes.get(status.lower(), 'badge-secondary')

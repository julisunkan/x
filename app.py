import os
import logging
from flask import Flask, render_template, redirect, url_for, session, request, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# SQLAlchemy Base Class
class Base(DeclarativeBase):
    pass

# Flask extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()
babel = Babel()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database Configuration
database_url = os.environ.get("DATABASE_URL") or "sqlite:///digitalskeletoncoin.db"
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# File Upload Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Localization
app.config['LANGUAGES'] = {'en': 'English', 'es': 'Español', 'fr': 'Français', 'de': 'Deutsch', 'zh': '中文'}
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'

# Init extensions
db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)
babel.init_app(app)

# Login Manager Config
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User.query.get(int(user_id))

# Maintenance Mode Middleware
@app.before_request
def check_maintenance_mode():
    from flask import current_app
    from models.settings import AppSettings

    if request.endpoint and request.endpoint.startswith('static'):
        return
    if request.endpoint in ['auth.login', 'auth.logout']:
        return
    if request.endpoint and request.endpoint.startswith('admin.') and current_user.is_authenticated and current_user.is_admin:
        return
    try:
        settings = AppSettings.get_settings()
        if settings.maintenance_mode:
            if current_user.is_authenticated and current_user.is_admin:
                return
            return render_template('maintenance.html', message=settings.maintenance_message or "Platform under maintenance."), 503
    except Exception as e:
        current_app.logger.error(f"Error checking maintenance mode: {str(e)}")
        return

# Babel locale selector
def get_locale():
    if 'language' in session:
        return session['language']
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'en'

babel.locale_selector_func = get_locale

@app.context_processor
def inject_app_settings():
    from models.settings import AppSettings
    return dict(app_settings=AppSettings.get_settings())

# Blueprints
from core.auth import auth_bp
from core.mining import mining_bp
from core.tasks import tasks_bp
from core.admin import admin_bp
from core.promotions import promotions_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(mining_bp, url_prefix='/mining')
app.register_blueprint(tasks_bp, url_prefix='/tasks')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(promotions_bp)

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    from models.user import User
    from models.mining import MiningSession
    from models.task import Task, TaskCompletion
    from models.referral import Referral
    from sqlalchemy import func

    total_mined = db.session.query(func.sum(MiningSession.coins_earned)).filter_by(user_id=current_user.id).scalar() or 0
    completed_tasks = TaskCompletion.query.filter_by(user_id=current_user.id, status='approved').count()
    referral_count = Referral.query.filter_by(referrer_id=current_user.id).count()
    recent_mining = MiningSession.query.filter_by(user_id=current_user.id).order_by(MiningSession.created_at.desc()).limit(5).all()
    completed_task_ids = [tc.task_id for tc in TaskCompletion.query.filter_by(user_id=current_user.id).all()]
    available_tasks = Task.query.filter(~Task.id.in_(completed_task_ids), Task.is_active == True).limit(3).all()
    if current_user.is_admin:
        recent_task_completions = TaskCompletion.query.order_by(TaskCompletion.submitted_at.desc()).limit(5).all()
    else:
        recent_task_completions = TaskCompletion.query.filter_by(user_id=current_user.id).order_by(TaskCompletion.submitted_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                           total_mined=total_mined,
                           completed_tasks=completed_tasks,
                           referral_count=referral_count,
                           recent_mining=recent_mining,
                           available_tasks=available_tasks,
                           recent_task_completions=recent_task_completions)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/set_language/<language>')
def set_language(language=None):
    session['language'] = language
    return redirect(request.referrer or url_for('index'))

@app.route('/referrals')
@login_required
def referrals():
    from models.referral import Referral
    from models.user import User
    referrals = db.session.query(Referral, User).join(User, Referral.referred_id == User.id).filter(Referral.referrer_id == current_user.id).all()
    total_earnings = sum([r.Referral.earnings for r in referrals])
    return render_template('referrals.html', referrals=referrals, total_earnings=total_earnings)

@app.route('/withdrawals', methods=['GET', 'POST'])
@login_required
def withdrawals():
    from models.withdrawal import Withdrawal
    from forms import WithdrawalForm
    from datetime import datetime

    if request.method == 'POST':
        form = WithdrawalForm(request.form)
        if form.validate():
            if current_user.balance < form.amount.data:
                flash('Insufficient balance for withdrawal.', 'error')
                return redirect(url_for('withdrawals'))
            if form.amount.data < 100.0:
                flash('Minimum withdrawal amount is 100 coins.', 'error')
                return redirect(url_for('withdrawals'))

            withdrawal = Withdrawal(
                user_id=current_user.id,
                amount=form.amount.data,
                withdrawal_method=form.withdrawal_method.data,
                payment_address=form.payment_address.data,
                payment_details=form.payment_details.data,
                status='pending',
                requested_at=datetime.utcnow()
            )
            try:
                db.session.add(withdrawal)
                db.session.commit()
                flash('Withdrawal request submitted successfully.', 'success')
            except Exception:
                db.session.rollback()
                flash('Error submitting withdrawal request.', 'error')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'error')
        return redirect(url_for('withdrawals'))

    user_withdrawals = Withdrawal.query.filter_by(user_id=current_user.id).order_by(Withdrawal.requested_at.desc()).all()
    return render_template('withdrawals.html', withdrawals=user_withdrawals)

@app.route('/airdrops')
@login_required
def airdrops():
    from models.airdrop import Airdrop, AirdropParticipation
    from datetime import datetime
    active_airdrops = Airdrop.query.filter(
        Airdrop.is_active == True,
        Airdrop.start_date <= datetime.utcnow(),
        Airdrop.end_date >= datetime.utcnow()
    ).all()
    participations = AirdropParticipation.query.filter_by(user_id=current_user.id).all()
    return render_template('airdrops.html', airdrops=active_airdrops, participations={p.airdrop_id: p for p in participations})

@app.route('/airdrops/join/<int:airdrop_id>', methods=['POST'])
@login_required
def join_airdrop(airdrop_id):
    from models.airdrop import Airdrop, AirdropParticipation
    airdrop = Airdrop.query.get_or_404(airdrop_id)

    if not airdrop.is_currently_active:
        flash('This airdrop is not currently active.', 'error')
    elif AirdropParticipation.query.filter_by(user_id=current_user.id, airdrop_id=airdrop_id).first():
        flash('You have already joined this airdrop.', 'warning')
    elif not airdrop.check_user_eligibility(current_user)['eligible']:
        flash('You are not eligible to join this airdrop.', 'error')
    elif airdrop.max_participants and airdrop.current_participants >= airdrop.max_participants:
        flash('This airdrop is full.', 'error')
    else:
        participation = AirdropParticipation(
            user_id=current_user.id,
            airdrop_id=airdrop_id,
            coins_received=airdrop.coins_per_user
        )
        airdrop.current_participants += 1
        try:
            db.session.add(participation)
            db.session.commit()
            flash(f'Joined airdrop! You will receive {airdrop.coins_per_user} coins.', 'success')
        except Exception:
            db.session.rollback()
            flash('An error occurred while joining the airdrop.', 'error')

    return redirect(url_for('airdrops'))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Table Initialization + Admin User
def create_tables():
    with app.app_context():
        from models import user, mining, task, referral, withdrawal, airdrop, promotion
        db.create_all()
        from models.user import User
        from werkzeug.security import generate_password_hash

        try:
            existing_admin = User.query.filter_by(email='admin@digitalskeletoncoin.com').first()
            if not existing_admin:
                admin_user = User(
                    username='admin',
                    email='admin@digitalskeletoncoin.com',
                    password_hash=generate_password_hash('admin123'),
                    is_admin=True,
                    email_verified=True,  # Admin user is pre-verified
                    balance=1000000,
                    xp=10000,
                    level=10
                )
                db.session.add(admin_user)
                db.session.commit()
                logging.info("✅ Admin user created: admin / admin123")
            else:
                # Ensure existing admin is email verified
                if not existing_admin.email_verified:
                    existing_admin.email_verified = True
                    db.session.commit()
                    logging.info("ℹ️ Admin user email verification updated.")
                logging.info("ℹ️ Admin user already exists. Skipping creation.")
        except Exception as e:
            db.session.rollback()
            logging.error(f"❌ Error creating admin user: {e}")

        try:
            users_without_avatars = User.query.filter_by(profile_image=None).all()
            for user in users_without_avatars:
                if user.username:
                    user.profile_image = user._generate_default_avatar()
            if users_without_avatars:
                db.session.commit()
                logging.info(f"✅ Updated {len(users_without_avatars)} users with default avatars.")
        except Exception as e:
            db.session.rollback()
            logging.error(f"❌ Error updating avatars: {e}")

        # Initialize promotion platforms and types
        try:
            from models.promotion import SocialPlatform, PromotionType
            
            # Create social platforms if they don't exist
            platforms_data = [
                {'name': 'X (Twitter)', 'icon_class': 'fab fa-x-twitter'},
                {'name': 'Instagram', 'icon_class': 'fab fa-instagram'},
                {'name': 'TikTok', 'icon_class': 'fab fa-tiktok'},
                {'name': 'YouTube', 'icon_class': 'fab fa-youtube'},
                {'name': 'Facebook', 'icon_class': 'fab fa-facebook'},
                {'name': 'LinkedIn', 'icon_class': 'fab fa-linkedin'},
                {'name': 'Telegram', 'icon_class': 'fab fa-telegram'},
                {'name': 'Website', 'icon_class': 'fas fa-globe'},
            ]
            
            for platform_data in platforms_data:
                existing_platform = SocialPlatform.query.filter_by(name=platform_data['name']).first()
                if not existing_platform:
                    platform = SocialPlatform(**platform_data)
                    db.session.add(platform)
            
            # Create promotion types if they don't exist
            promo_types_data = [
                {'name': 'Visit', 'description': 'Visit your profile or website'},
                {'name': 'Follow', 'description': 'Follow your account'},
                {'name': 'Like', 'description': 'Like your posts'},
                {'name': 'Share', 'description': 'Share your content'},
                {'name': 'Subscribe', 'description': 'Subscribe to your channel'},
                {'name': 'Comment', 'description': 'Comment on your posts'},
                {'name': 'Engage', 'description': 'General engagement with your content'},
            ]
            
            for promo_type_data in promo_types_data:
                existing_type = PromotionType.query.filter_by(name=promo_type_data['name']).first()
                if not existing_type:
                    promo_type = PromotionType(**promo_type_data)
                    db.session.add(promo_type)
            
            db.session.commit()
            logging.info("✅ Promotion platforms and types initialized.")
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"❌ Error initializing promotion data: {e}")

# Run setup
create_tables()

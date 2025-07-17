from datetime import datetime
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    
    # Profile information
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))

    
    # Game stats
    balance = db.Column(db.Float, default=0.0)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    mining_power = db.Column(db.Float, default=1.0)
    
    # Account status
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(255))
    email_verification_expires = db.Column(db.DateTime)
    password_reset_token = db.Column(db.String(255))
    password_reset_expires = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_mining = db.Column(db.DateTime)
    
    # Daily mission tracking
    daily_mission_date = db.Column(db.Date)
    daily_missions_completed = db.Column(db.Integer, default=0)
    
    # Referral code
    referral_code = db.Column(db.String(16), unique=True)
    referred_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Wallet information
    wallet_address = db.Column(db.String(200))
    wallet_type = db.Column(db.String(50))  # 'paypal', 'bank', 'crypto'
    profile_image = db.Column(db.String(255))  # path to profile image
    
    # Relationships
    mining_sessions = db.relationship('MiningSession', backref='user', lazy='dynamic')
    task_completions = db.relationship('TaskCompletion', foreign_keys='TaskCompletion.user_id', backref='user', lazy='dynamic')
    task_reviews = db.relationship('TaskCompletion', foreign_keys='TaskCompletion.reviewed_by', backref='task_reviewer', lazy='dynamic')
    withdrawals = db.relationship('Withdrawal', foreign_keys='Withdrawal.user_id', backref='user', lazy='dynamic')
    withdrawal_reviews = db.relationship('Withdrawal', foreign_keys='Withdrawal.reviewed_by', backref='withdrawal_reviewer', lazy='dynamic')
    airdrop_participations = db.relationship('AirdropParticipation', backref='user', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        if not self.profile_image and self.username:
            self.profile_image = self._generate_default_avatar()
    
    def generate_referral_code(self):
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def generate_verification_token(self):
        """Generate a secure token for email verification"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def generate_password_reset_token(self):
        """Generate a secure token for password reset"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _generate_default_avatar(self):
        """Generate a default avatar filename based on username"""
        import hashlib
        # Use username to create consistent avatar assignment
        hash_val = int(hashlib.md5(self.username.encode()).hexdigest(), 16)
        avatar_num = (hash_val % 6) + 1
        return f"default-avatar-{avatar_num}.svg"
    
    def get_profile_image_url(self):
        """Get the URL for user's profile image"""
        if self.profile_image:
            if self.profile_image.startswith('default-avatar-'):
                return f"/static/images/{self.profile_image}"
            else:
                return f"/static/uploads/profiles/{self.profile_image}"
        return "/static/images/default-avatar.svg"
    
    @property
    def profile_image_url(self):
        """Property for easy template access"""
        return self.get_profile_image_url()
    
    @property
    def avatar_url(self):
        """Alias for profile_image_url for template compatibility"""
        return self.get_profile_image_url()
    
    def is_verification_token_valid(self, token):
        """Check if email verification token is valid and not expired"""
        from datetime import datetime
        if not self.email_verification_token or not self.email_verification_expires:
            return False
        return (self.email_verification_token == token and 
                self.email_verification_expires > datetime.utcnow())
    
    def is_password_reset_token_valid(self, token):
        """Check if password reset token is valid and not expired"""
        from datetime import datetime
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        return (self.password_reset_token == token and 
                self.password_reset_expires > datetime.utcnow())
    
    @property
    def xp_for_next_level(self):
        return self.level * 1000
    
    @property
    def xp_progress(self):
        current_level_xp = (self.level - 1) * 1000
        next_level_xp = self.level * 1000
        progress_xp = self.xp - current_level_xp
        total_xp_needed = next_level_xp - current_level_xp
        return (progress_xp / total_xp_needed) * 100 if total_xp_needed > 0 else 0
    
    def add_xp(self, amount):
        self.xp += amount
        # Check for level up
        while self.xp >= self.xp_for_next_level:
            self.level += 1
            self.mining_power += 0.1  # Increase mining power with level
    
    def can_mine(self):
        if not self.last_mining:
            return True
        from datetime import datetime, timedelta
        return datetime.utcnow() - self.last_mining >= timedelta(seconds=1)  # 1 second cooldown
    
    def __repr__(self):
        return f'<User {self.username}>'

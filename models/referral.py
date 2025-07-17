from datetime import datetime
from app import db

class Referral(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    referred_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Referral details
    referral_code = db.Column(db.String(16), nullable=False)
    earnings = db.Column(db.Float, default=0.0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    referrer = db.relationship('User', foreign_keys=[referrer_id], backref='referrals_made')
    referred = db.relationship('User', foreign_keys=[referred_id], backref='referral_info')
    
    def __repr__(self):
        return f'<Referral {self.referrer_id} -> {self.referred_id}>'

class ReferralEarning(db.Model):
    """Track individual earning events from referrals"""
    id = db.Column(db.Integer, primary_key=True)
    referral_id = db.Column(db.Integer, db.ForeignKey('referral.id'), nullable=False)
    
    # Earning details
    amount = db.Column(db.Float, nullable=False)
    earning_type = db.Column(db.String(50), nullable=False)  # 'signup', 'mining', 'task_completion'
    description = db.Column(db.String(200))
    
    # Related activity
    related_mining_session_id = db.Column(db.Integer, db.ForeignKey('mining_session.id'))
    related_task_completion_id = db.Column(db.Integer, db.ForeignKey('task_completion.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    referral = db.relationship('Referral', backref='earning_records')
    
    def __repr__(self):
        return f'<ReferralEarning {self.id}: {self.amount}>'

class ReferralSettings(db.Model):
    """Global settings for the referral system"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Commission rates (as percentages)
    signup_bonus = db.Column(db.Float, default=10.0)  # Bonus for referrer when someone signs up
    mining_commission = db.Column(db.Float, default=5.0)  # % of referred user's mining
    task_commission = db.Column(db.Float, default=10.0)  # % of referred user's task rewards
    
    # Limits
    max_referrals_per_user = db.Column(db.Integer)  # None = unlimited
    min_withdrawal_amount = db.Column(db.Float, default=100.0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Admin tracking
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_settings(cls):
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def __repr__(self):
        return f'<ReferralSettings {self.id}>'

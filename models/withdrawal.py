from datetime import datetime
from app import db

class Withdrawal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Withdrawal details
    amount = db.Column(db.Float, nullable=False)
    withdrawal_method = db.Column(db.String(50), nullable=False)  # 'paypal', 'bank', 'crypto'
    
    # Payment details (encrypted in production)
    payment_address = db.Column(db.String(200), nullable=False)
    payment_details = db.Column(db.Text)  # JSON string with additional details
    
    # Status tracking
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected', 'paid'
    
    # Admin processing
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_at = db.Column(db.DateTime)
    admin_notes = db.Column(db.Text)
    
    # Transaction tracking
    transaction_id = db.Column(db.String(100))
    transaction_hash = db.Column(db.String(200))  # For crypto transactions
    
    # Timestamps
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    def approve(self, reviewer_id=None, notes=None, transaction_id=None):
        self.status = 'approved'
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow()
        self.admin_notes = notes
        self.transaction_id = transaction_id
        
        # Deduct amount from user balance
        self.user.balance -= self.amount
    
    def reject(self, reviewer_id=None, notes=None):
        self.status = 'rejected'
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow()
        self.admin_notes = notes
    
    def mark_paid(self, transaction_hash=None):
        self.status = 'paid'
        self.processed_at = datetime.utcnow()
        self.transaction_hash = transaction_hash
    
    def __repr__(self):
        return f'<Withdrawal {self.id}: {self.amount} ({self.status})>'

class WithdrawalSettings(db.Model):
    """Global settings for the withdrawal system"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Limits
    min_withdrawal_amount = db.Column(db.Float, default=100.0)
    max_withdrawal_amount = db.Column(db.Float, default=10000.0)
    daily_withdrawal_limit = db.Column(db.Float, default=1000.0)
    
    # Fees
    withdrawal_fee_percentage = db.Column(db.Float, default=2.0)
    withdrawal_fee_fixed = db.Column(db.Float, default=1.0)
    
    # Processing
    auto_approval_threshold = db.Column(db.Float, default=50.0)  # Auto-approve below this amount
    processing_time_hours = db.Column(db.Integer, default=24)
    
    # Status
    withdrawals_enabled = db.Column(db.Boolean, default=True)
    
    # Supported methods
    paypal_enabled = db.Column(db.Boolean, default=True)
    bank_transfer_enabled = db.Column(db.Boolean, default=True)
    crypto_enabled = db.Column(db.Boolean, default=False)
    
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
    
    def calculate_fee(self, amount):
        """Calculate withdrawal fee for given amount"""
        percentage_fee = amount * (self.withdrawal_fee_percentage / 100)
        total_fee = percentage_fee + self.withdrawal_fee_fixed
        return total_fee
    
    def calculate_net_amount(self, amount):
        """Calculate net amount after fees"""
        return amount - self.calculate_fee(amount)
    
    def __repr__(self):
        return f'<WithdrawalSettings {self.id}>'

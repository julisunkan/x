from datetime import datetime, timedelta
from app import db
from sqlalchemy import Enum
import uuid

class SocialPlatform(db.Model):
    """Social media platforms available for promotion"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # X, Instagram, TikTok, Website, etc.
    icon_class = db.Column(db.String(50))  # Font Awesome icon class
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    promotions = db.relationship('SocialPromotion', backref='social_platform', lazy=True)
    
    def __repr__(self):
        return f'<SocialPlatform {self.name}>'

class PromotionType(db.Model):
    """Types of promotion available"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # Visit, Like, Follow, Share, etc.
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    promotions = db.relationship('SocialPromotion', backref='promotion_type', lazy=True)
    
    def __repr__(self):
        return f'<PromotionType {self.name}>'

class SocialPromotion(db.Model):
    """User promotion campaigns"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Campaign details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    social_url = db.Column(db.String(500), nullable=False)  # URL to promote
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    platform_id = db.Column(db.Integer, db.ForeignKey('social_platform.id'), nullable=False)
    promotion_type_id = db.Column(db.Integer, db.ForeignKey('promotion_type.id'), nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='user_promotions', lazy='joined')
    
    # Budget and duration
    budget = db.Column(db.Float, nullable=False)  # Budget in USD
    days_duration = db.Column(db.Integer, nullable=False)  # Calculated from budget ($5 = 1 day)
    
    # Campaign dates
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, active, completed, cancelled
    is_approved = db.Column(db.Boolean, default=False)
    
    # Payment tracking
    invoice_number = db.Column(db.String(50), unique=True)
    is_paid = db.Column(db.Boolean, default=False)
    payment_proof = db.Column(db.String(200))  # File path to payment proof
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    paid_at = db.Column(db.DateTime)
    
    # Admin notes
    admin_notes = db.Column(db.Text)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        if self.budget:
            self.days_duration = max(1, int(self.budget // 5))  # $5 per day
            
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        timestamp = datetime.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"DSC-{timestamp}-{unique_id}"
    
    def calculate_end_date(self):
        """Calculate campaign end date based on start date and duration"""
        if self.start_date:
            return self.start_date + timedelta(days=self.days_duration)
        return None
    
    def start_campaign(self):
        """Start the promotion campaign"""
        self.start_date = datetime.utcnow()
        self.end_date = self.calculate_end_date()
        self.status = 'active'
        self.updated_at = datetime.utcnow()
    
    def complete_campaign(self):
        """Mark campaign as completed"""
        self.status = 'completed'
        self.updated_at = datetime.utcnow()
    
    def mark_as_paid(self):
        """Mark promotion as paid"""
        self.is_paid = True
        self.paid_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @property
    def is_active(self):
        """Check if campaign is currently active"""
        if self.status != 'active' or not self.start_date or not self.end_date:
            return False
        now = datetime.utcnow()
        return self.start_date <= now <= self.end_date
    
    @property
    def days_remaining(self):
        """Calculate days remaining in campaign"""
        if not self.end_date or self.status != 'active':
            return 0
        now = datetime.utcnow()
        if now > self.end_date:
            return 0
        return (self.end_date - now).days + 1
    
    def __repr__(self):
        return f'<SocialPromotion {self.title} - ${self.budget}>'

class PromotionSettings(db.Model):
    """Settings for promotion system"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Payment instructions
    payment_instructions = db.Column(db.Text, default='Please send payment to: [Bank Details]\nPayPal: admin@digitalskeletoncoin.com\nAfter payment, upload proof in your promotion dashboard.')
    
    # Pricing settings
    daily_rate = db.Column(db.Float, default=5.0)  # $5 per day
    min_budget = db.Column(db.Float, default=5.0)
    max_budget = db.Column(db.Float, default=1000.0)
    
    # Business details for invoices
    business_name = db.Column(db.String(200), default='DigitalSkeletonCoin (DSC) Promotions')
    business_address = db.Column(db.Text)
    business_email = db.Column(db.String(100), default='promotions@digitalskeletoncoin.com')
    business_phone = db.Column(db.String(50))
    tax_id = db.Column(db.String(50))
    
    # Auto-approval settings
    auto_approve_under = db.Column(db.Float, default=50.0)  # Auto-approve campaigns under $50
    require_manual_review = db.Column(db.Boolean, default=True)
    
    # Terms and conditions
    terms_and_conditions = db.Column(db.Text, default='1. Payment must be received before campaign activation.\n2. Campaigns run for specified duration only.\n3. Refunds available within 24 hours of payment.\n4. DSC reserves the right to reject inappropriate content.')
    
    # Timestamps
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_settings(cls):
        """Get or create promotion settings"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def __repr__(self):
        return f'<PromotionSettings ${self.daily_rate}/day>'
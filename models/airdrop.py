from datetime import datetime
from app import db

class Airdrop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Airdrop details
    total_coins = db.Column(db.Float, nullable=False)
    coins_per_user = db.Column(db.Float, nullable=False)
    max_participants = db.Column(db.Integer)
    current_participants = db.Column(db.Integer, default=0)
    
    # Requirements
    min_level = db.Column(db.Integer, default=1)
    min_balance = db.Column(db.Float, default=0.0)
    min_referrals = db.Column(db.Integer, default=0)
    requires_task_completion = db.Column(db.Boolean, default=False)
    required_task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    
    # Timing
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    distribution_date = db.Column(db.DateTime)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_distributed = db.Column(db.Boolean, default=False)
    
    # Admin info
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    participations = db.relationship('AirdropParticipation', backref='airdrop', lazy='dynamic')
    required_task = db.relationship('Task', backref='required_for_airdrops')
    
    @property
    def is_currently_active(self):
        now = datetime.utcnow()
        return self.is_active and self.start_date <= now <= self.end_date
    
    @property
    def can_participate(self):
        if not self.is_currently_active:
            return False
        if self.max_participants and self.current_participants >= self.max_participants:
            return False
        return True
    
    def check_user_eligibility(self, user):
        """Check if user meets all requirements for this airdrop"""
        if user.level < self.min_level:
            return {'eligible': False, 'reason': f"Minimum level required: {self.min_level}"}
        
        if user.balance < self.min_balance:
            return {'eligible': False, 'reason': f"Minimum balance required: {self.min_balance}"}
        
        if self.min_referrals > 0:
            from models.referral import Referral
            referral_count = Referral.query.filter_by(referrer_id=user.id).count()
            if referral_count < self.min_referrals:
                return {'eligible': False, 'reason': f"Minimum referrals required: {self.min_referrals}"}
        
        if self.requires_task_completion and self.required_task_id:
            from models.task import TaskCompletion
            completion = TaskCompletion.query.filter_by(
                user_id=user.id, 
                task_id=self.required_task_id, 
                status='approved'
            ).first()
            if not completion:
                return {'eligible': False, 'reason': "Required task must be completed"}
        
        return {'eligible': True, 'reason': "Eligible"}
    
    def __repr__(self):
        return f'<Airdrop {self.title}>'

class AirdropParticipation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    airdrop_id = db.Column(db.Integer, db.ForeignKey('airdrop.id'), nullable=False)
    
    # Participation details
    participated_at = db.Column(db.DateTime, default=datetime.utcnow)
    coins_received = db.Column(db.Float, default=0.0)
    
    # Distribution status
    is_distributed = db.Column(db.Boolean, default=False)
    distributed_at = db.Column(db.DateTime)
    
    def distribute_coins(self):
        """Distribute coins to the user"""
        if not self.is_distributed:
            self.user.balance += self.airdrop.coins_per_user
            self.coins_received = self.airdrop.coins_per_user
            self.is_distributed = True
            self.distributed_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<AirdropParticipation {self.id}>'

class AirdropTemplate(db.Model):
    """Templates for creating airdrops quickly"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Default values
    default_coins_per_user = db.Column(db.Float, default=50.0)
    default_max_participants = db.Column(db.Integer, default=1000)
    default_min_level = db.Column(db.Integer, default=1)
    default_duration_days = db.Column(db.Integer, default=7)
    
    # Template settings
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AirdropTemplate {self.name}>'

from datetime import datetime
from app import db

class MiningSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Mining details
    clicks = db.Column(db.Integer, default=1)
    coins_earned = db.Column(db.Float, nullable=False)
    xp_earned = db.Column(db.Integer, default=1)
    
    # Session info
    session_duration = db.Column(db.Float)  # in seconds
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MiningSession {self.id}: {self.coins_earned} coins>'

class MiningEvent(db.Model):
    """Track special mining events and bonuses"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Event parameters
    multiplier = db.Column(db.Float, default=1.0)
    bonus_coins = db.Column(db.Float, default=0.0)
    bonus_xp = db.Column(db.Integer, default=0)
    
    # Timing
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Admin info
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_currently_active(self):
        now = datetime.utcnow()
        return self.is_active and self.start_time <= now <= self.end_time
    
    def __repr__(self):
        return f'<MiningEvent {self.name}>'

class DailyMission(db.Model):
    """Daily missions for users to complete"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Mission requirements
    mission_type = db.Column(db.String(50), nullable=False)  # 'mine', 'tasks', 'referrals'
    target_amount = db.Column(db.Integer, nullable=False)
    
    # Rewards
    coin_reward = db.Column(db.Float, default=0.0)
    xp_reward = db.Column(db.Integer, default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DailyMission {self.name}>'

class DailyMissionCompletion(db.Model):
    """Track user completion of daily missions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mission_id = db.Column(db.Integer, db.ForeignKey('daily_mission.id'), nullable=False)
    
    # Completion details
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    progress = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)
    
    # Rewards claimed
    rewards_claimed = db.Column(db.Boolean, default=False)
    
    # Relationships
    mission = db.relationship('DailyMission', backref='completions')
    
    def __repr__(self):
        return f'<DailyMissionCompletion {self.id}>'

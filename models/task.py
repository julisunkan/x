from datetime import datetime
from app import db

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Task details
    task_type = db.Column(db.String(50), nullable=False)  # 'like', 'follow', 'share', 'subscribe'
    platform = db.Column(db.String(50))  # 'twitter', 'telegram', 'youtube', 'instagram'
    url = db.Column(db.String(500))
    
    # Requirements
    requires_proof = db.Column(db.Boolean, default=True)
    proof_instructions = db.Column(db.Text)
    
    # Rewards
    coin_reward = db.Column(db.Float, nullable=False)
    xp_reward = db.Column(db.Integer, default=0)
    
    # Limits
    max_completions = db.Column(db.Integer)  # None = unlimited
    current_completions = db.Column(db.Integer, default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    requires_admin_approval = db.Column(db.Boolean, default=True)
    
    # Admin info
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    completions = db.relationship('TaskCompletion', backref='task', lazy='dynamic')
    
    @property
    def is_available(self):
        if not self.is_active:
            return False
        if self.max_completions and self.current_completions >= self.max_completions:
            return False
        return True
    
    def __repr__(self):
        return f'<Task {self.title}>'

class TaskCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    
    # Submission details
    proof_text = db.Column(db.Text)
    proof_image_url = db.Column(db.String(500))
    proof_file_path = db.Column(db.String(500))
    
    # Status tracking
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    
    # AI verification (if enabled)
    ai_verification_score = db.Column(db.Float)
    ai_verification_notes = db.Column(db.Text)
    
    # Admin review
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_at = db.Column(db.DateTime)
    review_notes = db.Column(db.Text)
    
    # Timestamps
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def approve(self, reviewer_id=None, notes=None):
        self.status = 'approved'
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow()
        self.review_notes = notes
        self.completed_at = datetime.utcnow()
        
        # Award rewards to user
        self.user.balance += self.task.coin_reward
        if self.task.xp_reward:
            self.user.add_xp(self.task.xp_reward)
        
        # Update task completion count
        self.task.current_completions += 1
    
    def reject(self, reviewer_id=None, notes=None):
        self.status = 'rejected'
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow()
        self.review_notes = notes
    
    def __repr__(self):
        return f'<TaskCompletion {self.id}: {self.status}>'

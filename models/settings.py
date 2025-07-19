from datetime import datetime
from app import db

class AppSettings(db.Model):
    """Global application settings"""
    id = db.Column(db.Integer, primary_key=True)
    
    # App branding
    app_name = db.Column(db.String(100), default='DigitalSkeletonCoin (DSC) Mining Platform')
    app_description = db.Column(db.Text, default='A gamified cryptocurrency mining platform')
    app_logo = db.Column(db.String(200))  # URL or path to logo
    
    # Theme settings
    primary_color = db.Column(db.String(7), default='#0d6efd')  # Bootstrap primary
    secondary_color = db.Column(db.String(7), default='#6c757d')  # Bootstrap secondary
    success_color = db.Column(db.String(7), default='#198754')  # Bootstrap success
    warning_color = db.Column(db.String(7), default='#ffc107')  # Bootstrap warning
    danger_color = db.Column(db.String(7), default='#dc3545')  # Bootstrap danger
    
    # SMTP settings
    smtp_server = db.Column(db.String(100))
    smtp_port = db.Column(db.Integer, default=587)
    smtp_username = db.Column(db.String(100))
    smtp_password = db.Column(db.String(200))
    smtp_use_tls = db.Column(db.Boolean, default=True)
    smtp_from_email = db.Column(db.String(100))
    smtp_from_name = db.Column(db.String(100))
    
    # Contact information
    contact_email = db.Column(db.String(100))
    support_email = db.Column(db.String(100))
    
    # Social media links
    twitter_url = db.Column(db.String(200))
    telegram_url = db.Column(db.String(200))
    discord_url = db.Column(db.String(200))
    
    # Maintenance mode
    maintenance_mode = db.Column(db.Boolean, default=False)
    maintenance_message = db.Column(db.Text)
    
    # System settings
    max_upload_size = db.Column(db.Integer, default=5)  # MB
    session_timeout = db.Column(db.Integer, default=30)  # days
    
    # Timestamps
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_settings(cls):
        """Get or create application settings"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def __repr__(self):
        return f'<AppSettings {self.app_name}>'

class DatabaseBackup(db.Model):
    """Track database backups"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    file_size = db.Column(db.Integer)  # bytes
    backup_type = db.Column(db.String(20), default='manual')  # manual, automatic
    
    # Backup metadata
    tables_count = db.Column(db.Integer)
    records_count = db.Column(db.Integer)
    
    # Status
    status = db.Column(db.String(20), default='completed')  # completed, failed, in_progress
    error_message = db.Column(db.Text)
    
    # Timestamps
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DatabaseBackup {self.filename}>'
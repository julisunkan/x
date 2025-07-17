# Models package
# Import all models to ensure they're registered with SQLAlchemy
from . import user, task, mining, referral, withdrawal, airdrop, settings

__all__ = ['user', 'task', 'mining', 'referral', 'withdrawal', 'airdrop', 'settings']

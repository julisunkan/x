from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from models.mining import MiningSession, MiningEvent, DailyMission, DailyMissionCompletion
from models.referral import Referral, ReferralEarning, ReferralSettings
from utils.helpers import get_client_ip
import random
import logging

mining_bp = Blueprint('mining', __name__)

@mining_bp.route('/')
@login_required
def mining_page():
    # Get current mining events
    active_events = MiningEvent.query.filter(
        MiningEvent.is_active == True,
        MiningEvent.start_time <= datetime.utcnow(),
        MiningEvent.end_time >= datetime.utcnow()
    ).all()
    
    # Get daily missions
    today = datetime.utcnow().date()
    daily_missions = DailyMission.query.filter_by(is_active=True).all()
    
    # Get user's mission progress for today
    mission_progress = {}
    for mission in daily_missions:
        completion = DailyMissionCompletion.query.filter_by(
            user_id=current_user.id,
            mission_id=mission.id
        ).filter(
            db.func.date(DailyMissionCompletion.completed_at) == today
        ).first()
        
        if completion:
            mission_progress[mission.id] = completion.progress
        else:
            mission_progress[mission.id] = 0
    
    return render_template('mining.html', 
                         events=active_events, 
                         missions=daily_missions,
                         mission_progress=mission_progress)

@mining_bp.route('/mine', methods=['POST'])
@login_required
def mine():
    if not current_user.can_mine():
        return jsonify({'error': 'Mining cooldown active'}), 429
    
    # Base mining calculation
    base_coins = 1.0
    base_xp = 1
    
    # Apply user's mining power
    coins_earned = base_coins * current_user.mining_power
    xp_earned = base_xp
    
    # Apply active mining events
    active_events = MiningEvent.query.filter(
        MiningEvent.is_active == True,
        MiningEvent.start_time <= datetime.utcnow(),
        MiningEvent.end_time >= datetime.utcnow()
    ).all()
    
    event_multiplier = 1.0
    event_bonus_coins = 0.0
    event_bonus_xp = 0
    
    for event in active_events:
        event_multiplier *= event.multiplier
        event_bonus_coins += event.bonus_coins
        event_bonus_xp += event.bonus_xp
    
    # Apply event bonuses
    coins_earned = (coins_earned * event_multiplier) + event_bonus_coins
    xp_earned = (xp_earned * event_multiplier) + event_bonus_xp
    
    # Add some randomness (±10%)
    randomness = random.uniform(0.9, 1.1)
    coins_earned *= randomness
    
    # Round to reasonable precision
    coins_earned = round(coins_earned, 4)
    xp_earned = int(xp_earned)
    
    # Create mining session
    mining_session = MiningSession(
        user_id=current_user.id,
        coins_earned=coins_earned,
        xp_earned=xp_earned,
        ip_address=get_client_ip(),
        user_agent=request.user_agent.string[:255]
    )
    
    # Update user stats
    current_user.balance += coins_earned
    current_user.add_xp(xp_earned)
    current_user.last_mining = datetime.utcnow()
    
    db.session.add(mining_session)
    
    # Handle referral earnings
    if current_user.referred_by:
        referral = Referral.query.filter_by(
            referrer_id=current_user.referred_by,
            referred_id=current_user.id
        ).first()
        
        if referral and referral.is_active:
            settings = ReferralSettings.get_settings()
            referral_amount = coins_earned * (settings.mining_commission / 100)
            
            # Add to referrer's balance
            referrer = referral.referrer
            referrer.balance += referral_amount
            referral.earnings += referral_amount
            
            # Track the earning
            referral_earning = ReferralEarning(
                referral_id=referral.id,
                amount=referral_amount,
                earning_type='mining',
                description=f'Mining commission from {current_user.username}',
                related_mining_session_id=mining_session.id
            )
            db.session.add(referral_earning)
    
    # Update daily mission progress
    update_daily_mission_progress('mine', 1)
    
    try:
        db.session.commit()
        logging.debug(f"User {current_user.username} mined {coins_earned} coins, {xp_earned} XP")
        
        return jsonify({
            'success': True,
            'coins_earned': coins_earned,
            'xp_earned': xp_earned,
            'new_balance': current_user.balance,
            'new_xp': current_user.xp,
            'new_level': current_user.level,
            'xp_progress': current_user.xp_progress
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Mining error for user {current_user.username}: {str(e)}")
        return jsonify({'error': 'Mining failed'}), 500

@mining_bp.route('/claim-mission/<int:mission_id>', methods=['POST'])
@login_required
def claim_mission_reward(mission_id):
    mission = DailyMission.query.get_or_404(mission_id)
    today = datetime.utcnow().date()
    
    # Check if user has completed the mission today
    completion = DailyMissionCompletion.query.filter_by(
        user_id=current_user.id,
        mission_id=mission_id
    ).filter(
        db.func.date(DailyMissionCompletion.completed_at) == today
    ).first()
    
    if not completion or not completion.is_completed or completion.rewards_claimed:
        flash('Mission not completed or rewards already claimed.', 'error')
        return redirect(url_for('mining.mining_page'))
    
    # Award rewards
    current_user.balance += mission.coin_reward
    if mission.xp_reward:
        current_user.add_xp(mission.xp_reward)
    
    completion.rewards_claimed = True
    
    try:
        db.session.commit()
        flash(f'Mission rewards claimed! +{mission.coin_reward} coins, +{mission.xp_reward} XP', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Mission reward claim error: {str(e)}")
        flash('Error claiming mission rewards.', 'error')
    
    return redirect(url_for('mining.mining_page'))

def update_daily_mission_progress(mission_type, amount):
    """Update user's progress on daily missions"""
    today = datetime.utcnow().date()
    missions = DailyMission.query.filter_by(mission_type=mission_type, is_active=True).all()
    
    for mission in missions:
        # Get or create completion record for today
        completion = DailyMissionCompletion.query.filter_by(
            user_id=current_user.id,
            mission_id=mission.id
        ).filter(
            db.func.date(DailyMissionCompletion.completed_at) == today
        ).first()
        
        if not completion:
            completion = DailyMissionCompletion(
                user_id=current_user.id,
                mission_id=mission.id,
                progress=0
            )
            db.session.add(completion)
        
        # Update progress
        if not completion.is_completed:
            completion.progress += amount
            if completion.progress >= mission.target_amount:
                completion.progress = mission.target_amount
                completion.is_completed = True

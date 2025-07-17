from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from models.user import User
from models.task import Task, TaskCompletion
from models.withdrawal import Withdrawal, WithdrawalSettings
from models.airdrop import Airdrop, AirdropParticipation
from models.mining import MiningEvent, DailyMission
from models.referral import ReferralSettings
from models.settings import AppSettings, DatabaseBackup
from functools import wraps
import logging
import os
import json
import zipfile
import tempfile
from datetime import datetime
from sqlalchemy import inspect, text

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Get statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    pending_withdrawals = Withdrawal.query.filter_by(status='pending').count()
    pending_tasks = TaskCompletion.query.filter_by(status='pending').count()
    active_airdrops = Airdrop.query.filter_by(is_active=True).count()
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_withdrawals = Withdrawal.query.order_by(Withdrawal.requested_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         pending_withdrawals=pending_withdrawals,
                         pending_tasks=pending_tasks,
                         active_airdrops=active_airdrops,
                         recent_users=recent_users,
                         recent_withdrawals=recent_withdrawals)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(
            db.or_(
                User.username.contains(search),
                User.email.contains(search),
                User.first_name.contains(search),
                User.last_name.contains(search)
            )
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    action = 'activated' if user.is_active else 'deactivated'
    
    try:
        db.session.commit()
        flash(f'User {user.username} has been {action}.', 'success')
        logging.info(f"Admin {current_user.username} {action} user {user.username}")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error toggling user status: {str(e)}")
        flash('An error occurred.', 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/edit-balance', methods=['POST'])
@login_required
@admin_required
def edit_user_balance(user_id):
    user = User.query.get_or_404(user_id)
    new_balance = request.form.get('balance', type=float)
    
    if new_balance is None or new_balance < 0:
        flash('Invalid balance amount.', 'error')
        return redirect(url_for('admin.users'))
    
    old_balance = user.balance
    user.balance = new_balance
    
    try:
        db.session.commit()
        flash(f'User {user.username} balance updated from {old_balance} to {new_balance}.', 'success')
        logging.info(f"Admin {current_user.username} changed {user.username} balance from {old_balance} to {new_balance}")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating user balance: {str(e)}")
        flash('An error occurred.', 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    if user.is_admin:
        flash('You cannot delete another admin account.', 'error')
        return redirect(url_for('admin.users'))
    
    username = user.username
    
    try:
        # Delete related records first to maintain referential integrity
        from models.mining import MiningSession
        from models.task import TaskCompletion
        from models.withdrawal import Withdrawal
        from models.airdrop import AirdropParticipation
        from models.referral import Referral, ReferralEarning
        
        # Delete referral earnings for referrals where this user is involved
        referrals_as_referrer = Referral.query.filter_by(referrer_id=user_id).all()
        referrals_as_referred = Referral.query.filter_by(referred_id=user_id).all()
        
        for referral in referrals_as_referrer + referrals_as_referred:
            ReferralEarning.query.filter_by(referral_id=referral.id).delete()
        
        # Delete mining sessions
        MiningSession.query.filter_by(user_id=user_id).delete()
        
        # Delete task completions
        TaskCompletion.query.filter_by(user_id=user_id).delete()
        
        # Delete withdrawals
        Withdrawal.query.filter_by(user_id=user_id).delete()
        
        # Delete airdrop participations
        AirdropParticipation.query.filter_by(user_id=user_id).delete()
        
        # Delete referrals (both as referrer and referred)
        Referral.query.filter_by(referrer_id=user_id).delete()
        Referral.query.filter_by(referred_id=user_id).delete()
        
        # Finally delete the user
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User {username} has been deleted successfully.', 'success')
        logging.info(f"Admin {current_user.username} deleted user {username}")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting user {username}: {str(e)}")
        flash('An error occurred while deleting the user.', 'error')
    
    return redirect(url_for('admin.users'))



@admin_bp.route('/withdrawals')
@login_required
@admin_required
def withdrawals():
    status_filter = request.args.get('status', 'pending')
    page = request.args.get('page', 1, type=int)
    
    query = Withdrawal.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    withdrawals = query.order_by(Withdrawal.requested_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/withdrawals.html', 
                         withdrawals=withdrawals, 
                         status_filter=status_filter)

@admin_bp.route('/withdrawals/<int:withdrawal_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_withdrawal(withdrawal_id):
    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
    notes = request.form.get('notes', '')
    transaction_id = request.form.get('transaction_id', '')
    
    if withdrawal.status != 'pending':
        flash('Withdrawal has already been processed.', 'error')
        return redirect(url_for('admin.withdrawals'))
    
    # Check if user has sufficient balance
    if withdrawal.user.balance < withdrawal.amount:
        flash('User has insufficient balance for this withdrawal.', 'error')
        return redirect(url_for('admin.withdrawals'))
    
    withdrawal.approve(current_user.id, notes, transaction_id)
    
    try:
        db.session.commit()
        flash(f'Withdrawal approved for {withdrawal.user.username}.', 'success')
        logging.info(f"Admin {current_user.username} approved withdrawal {withdrawal.id}")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error approving withdrawal: {str(e)}")
        flash('An error occurred.', 'error')
    
    return redirect(url_for('admin.withdrawals'))

@admin_bp.route('/withdrawals/<int:withdrawal_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_withdrawal(withdrawal_id):
    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
    notes = request.form.get('notes', '')
    
    if withdrawal.status != 'pending':
        flash('Withdrawal has already been processed.', 'error')
        return redirect(url_for('admin.withdrawals'))
    
    withdrawal.reject(current_user.id, notes)
    
    try:
        db.session.commit()
        flash(f'Withdrawal rejected for {withdrawal.user.username}.', 'info')
        logging.info(f"Admin {current_user.username} rejected withdrawal {withdrawal.id}")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error rejecting withdrawal: {str(e)}")
        flash('An error occurred.', 'error')
    
    return redirect(url_for('admin.withdrawals'))

@admin_bp.route('/tasks')
@login_required
@admin_required
def tasks():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template('admin/tasks.html', tasks=tasks)

@admin_bp.route('/task-completions')
@login_required
@admin_required
def task_completions():
    status_filter = request.args.get('status', 'pending')
    page = request.args.get('page', 1, type=int)
    
    query = TaskCompletion.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    completions = query.order_by(TaskCompletion.submitted_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/task_completions.html', 
                         completions=completions, 
                         status_filter=status_filter)

@admin_bp.route('/task-completions/<int:completion_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_task_completion(completion_id):
    completion = TaskCompletion.query.get_or_404(completion_id)
    
    if completion.status != 'pending':
        flash('Task completion has already been processed.', 'error')
        return redirect(url_for('admin.task_completions'))
    
    completion.approve()
    
    try:
        db.session.commit()
        flash(f'Task completion approved for {completion.user.username}.', 'success')
        logging.info(f"Admin {current_user.username} approved task completion {completion.id}")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error approving task completion: {str(e)}")
        flash('An error occurred.', 'error')
    
    return redirect(url_for('admin.task_completions'))

@admin_bp.route('/task-completions/<int:completion_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_task_completion(completion_id):
    completion = TaskCompletion.query.get_or_404(completion_id)
    admin_notes = request.form.get('notes', '')
    
    if completion.status != 'pending':
        flash('Task completion has already been processed.', 'error')
        return redirect(url_for('admin.task_completions'))
    
    completion.reject(admin_notes)
    
    try:
        db.session.commit()
        flash(f'Task completion rejected for {completion.user.username}.', 'info')
        logging.info(f"Admin {current_user.username} rejected task completion {completion.id}")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error rejecting task completion: {str(e)}")
        flash('An error occurred.', 'error')
    
    return redirect(url_for('admin.task_completions'))

@admin_bp.route('/tasks/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_task():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        task_type = request.form.get('task_type')
        platform = request.form.get('platform')
        url = request.form.get('url')
        coin_reward = request.form.get('coin_reward', type=float)
        xp_reward = request.form.get('xp_reward', type=int)
        max_completions = request.form.get('max_completions', type=int)
        requires_proof = bool(request.form.get('requires_proof'))
        proof_instructions = request.form.get('proof_instructions')
        requires_admin_approval = bool(request.form.get('requires_admin_approval'))
        
        task = Task(
            title=title,
            description=description,
            task_type=task_type,
            platform=platform,
            url=url,
            coin_reward=coin_reward,
            xp_reward=xp_reward or 0,
            max_completions=max_completions,
            requires_proof=requires_proof,
            proof_instructions=proof_instructions,
            requires_admin_approval=requires_admin_approval,
            created_by=current_user.id
        )
        
        db.session.add(task)
        
        try:
            db.session.commit()
            flash('Task created successfully!', 'success')
            logging.info(f"Admin {current_user.username} created task: {title}")
            return redirect(url_for('admin.tasks'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating task: {str(e)}")
            flash('An error occurred while creating the task.', 'error')
    
    return render_template('admin/create_task.html')

@admin_bp.route('/tasks/<int:task_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.is_active = not task.is_active
    
    try:
        db.session.commit()
        status = 'activated' if task.is_active else 'deactivated'
        flash(f'Task "{task.title}" has been {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error toggling task: {str(e)}")
        flash('An error occurred.', 'error')
    
    return redirect(url_for('admin.tasks'))

@admin_bp.route('/tasks/<int:task_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check if task has any completions
    completion_count = TaskCompletion.query.filter_by(task_id=task_id).count()
    
    if completion_count > 0:
        flash(f'Cannot delete task "{task.title}" - it has {completion_count} completions.', 'error')
        return redirect(url_for('admin.tasks'))
    
    task_title = task.title
    
    try:
        db.session.delete(task)
        db.session.commit()
        flash(f'Task "{task_title}" has been deleted successfully.', 'success')
        logging.info(f"Admin {current_user.username} deleted task: {task_title}")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting task: {str(e)}")
        flash('An error occurred while deleting the task.', 'error')
    
    return redirect(url_for('admin.tasks'))

@admin_bp.route('/airdrops')
@login_required
@admin_required
def airdrops():
    airdrops = Airdrop.query.order_by(Airdrop.created_at.desc()).all()
    return render_template('admin/airdrops.html', airdrops=airdrops)

@admin_bp.route('/airdrops/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_airdrop():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        total_coins = request.form.get('total_coins', type=float)
        coins_per_user = request.form.get('coins_per_user', type=float)
        max_participants = request.form.get('max_participants', type=int)
        min_level = request.form.get('min_level', type=int)
        min_balance = request.form.get('min_balance', type=float)
        min_referrals = request.form.get('min_referrals', type=int)
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%dT%H:%M')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%dT%H:%M')
        
        airdrop = Airdrop(
            title=title,
            description=description,
            total_coins=total_coins,
            coins_per_user=coins_per_user,
            max_participants=max_participants,
            min_level=min_level or 1,
            min_balance=min_balance or 0.0,
            min_referrals=min_referrals or 0,
            start_date=start_date,
            end_date=end_date,
            created_by=current_user.id
        )
        
        db.session.add(airdrop)
        
        try:
            db.session.commit()
            flash('Airdrop created successfully!', 'success')
            logging.info(f"Admin {current_user.username} created airdrop: {title}")
            return redirect(url_for('admin.airdrops'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating airdrop: {str(e)}")
            flash('An error occurred while creating the airdrop.', 'error')
    
    return render_template('admin/create_airdrop.html')

@admin_bp.route('/airdrops/<int:airdrop_id>/toggle', methods=['GET', 'POST'])
@login_required
@admin_required
def toggle_airdrop(airdrop_id):
    airdrop = Airdrop.query.get_or_404(airdrop_id)
    airdrop.is_active = not airdrop.is_active
    
    try:
        db.session.commit()
        status = 'activated' if airdrop.is_active else 'deactivated'
        flash(f'Airdrop "{airdrop.title}" has been {status}.', 'success')
        logging.info(f"Admin {current_user.username} {status} airdrop: {airdrop.title}")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error toggling airdrop: {str(e)}")
        flash('An error occurred.', 'error')
    
    return redirect(url_for('admin.airdrops'))

@admin_bp.route('/airdrops/<int:airdrop_id>/distribute', methods=['GET', 'POST'])
@login_required
@admin_required
def distribute_airdrop(airdrop_id):
    airdrop = Airdrop.query.get_or_404(airdrop_id)
    
    if airdrop.is_distributed:
        flash(f'Airdrop "{airdrop.title}" has already been distributed.', 'error')
        return redirect(url_for('admin.airdrops'))
    
    # Get eligible participants
    participants = AirdropParticipation.query.filter_by(airdrop_id=airdrop_id, is_distributed=False).all()
    
    if not participants:
        flash(f'No participants found for airdrop "{airdrop.title}".', 'error')
        return redirect(url_for('admin.airdrops'))
    
    distributed_count = 0
    total_coins = 0
    
    try:
        for participation in participants:
            participation.distribute_coins()
            distributed_count += 1
            total_coins += participation.coins_received
        
        airdrop.is_distributed = True
        airdrop.distribution_date = datetime.utcnow()
        
        db.session.commit()
        flash(f'Airdrop "{airdrop.title}" distributed to {distributed_count} users ({total_coins} coins).', 'success')
        logging.info(f"Admin {current_user.username} distributed airdrop: {airdrop.title} to {distributed_count} users")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error distributing airdrop: {str(e)}")
        flash('An error occurred while distributing the airdrop.', 'error')
    
    return redirect(url_for('admin.airdrops'))

@admin_bp.route('/airdrops/<int:airdrop_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_airdrop(airdrop_id):
    airdrop = Airdrop.query.get_or_404(airdrop_id)
    
    # Check if airdrop has participants
    participant_count = AirdropParticipation.query.filter_by(airdrop_id=airdrop_id).count()
    
    if participant_count > 0:
        flash(f'Cannot delete airdrop "{airdrop.title}" - it has {participant_count} participants.', 'error')
        return redirect(url_for('admin.airdrops'))
    
    airdrop_title = airdrop.title
    
    try:
        db.session.delete(airdrop)
        db.session.commit()
        flash(f'Airdrop "{airdrop_title}" has been deleted successfully.', 'success')
        logging.info(f"Admin {current_user.username} deleted airdrop: {airdrop_title}")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting airdrop: {str(e)}")
        flash('An error occurred while deleting the airdrop.', 'error')
    
    return redirect(url_for('admin.airdrops'))

@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    withdrawal_settings = WithdrawalSettings.get_settings()
    referral_settings = ReferralSettings.get_settings()
    app_settings = AppSettings.get_settings()
    
    return render_template('admin/settings.html',
                         withdrawal_settings=withdrawal_settings,
                         referral_settings=referral_settings,
                         app_settings=app_settings)

@admin_bp.route('/settings/withdrawal', methods=['POST'])
@login_required
@admin_required
def update_withdrawal_settings():
    settings = WithdrawalSettings.get_settings()
    
    settings.min_withdrawal_amount = request.form.get('min_withdrawal_amount', type=float)
    settings.max_withdrawal_amount = request.form.get('max_withdrawal_amount', type=float)
    settings.withdrawal_fee_percentage = request.form.get('withdrawal_fee_percentage', type=float)
    settings.withdrawal_fee_fixed = request.form.get('withdrawal_fee_fixed', type=float)
    settings.withdrawals_enabled = bool(request.form.get('withdrawals_enabled'))
    settings.updated_by = current_user.id
    
    try:
        db.session.commit()
        flash('Withdrawal settings updated successfully!', 'success')
        logging.info(f"Admin {current_user.username} updated withdrawal settings")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating withdrawal settings: {str(e)}")
        flash('An error occurred.', 'error')
    
    return redirect(url_for('admin.settings'))

@admin_bp.route('/settings/referral', methods=['POST'])
@login_required
@admin_required
def update_referral_settings():
    settings = ReferralSettings.get_settings()
    
    settings.signup_bonus = request.form.get('signup_bonus', type=float)
    settings.mining_commission = request.form.get('mining_commission', type=float)
    settings.task_commission = request.form.get('task_commission', type=float)
    settings.is_active = bool(request.form.get('is_active'))
    settings.updated_by = current_user.id
    
    try:
        db.session.commit()
        flash('Referral settings updated successfully!', 'success')
        logging.info(f"Admin {current_user.username} updated referral settings")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating referral settings: {str(e)}")
        flash('An error occurred.', 'error')
    
    return redirect(url_for('admin.settings'))

@admin_bp.route('/settings/app', methods=['POST'])
@login_required
@admin_required
def update_app_settings():
    settings = AppSettings.get_settings()
    
    # App branding
    settings.app_name = request.form.get('app_name')
    settings.app_description = request.form.get('app_description')
    
    # Theme colors
    settings.primary_color = request.form.get('primary_color')
    settings.secondary_color = request.form.get('secondary_color')
    settings.success_color = request.form.get('success_color')
    settings.warning_color = request.form.get('warning_color')
    settings.danger_color = request.form.get('danger_color')
    
    # Contact info
    settings.contact_email = request.form.get('contact_email')
    settings.support_email = request.form.get('support_email')
    
    # Social media
    settings.twitter_url = request.form.get('twitter_url')
    settings.telegram_url = request.form.get('telegram_url')
    settings.discord_url = request.form.get('discord_url')
    
    # Maintenance mode
    settings.maintenance_mode = bool(request.form.get('maintenance_mode'))
    settings.maintenance_message = request.form.get('maintenance_message')
    
    settings.updated_by = current_user.id
    
    try:
        db.session.commit()
        flash('App settings updated successfully!', 'success')
        logging.info(f"Admin {current_user.username} updated app settings")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating app settings: {str(e)}")
        flash('An error occurred.', 'error')
    
    return redirect(url_for('admin.settings'))

@admin_bp.route('/settings/smtp', methods=['POST'])
@login_required
@admin_required
def update_smtp_settings():
    settings = AppSettings.get_settings()
    
    settings.smtp_server = request.form.get('smtp_server')
    settings.smtp_port = request.form.get('smtp_port', type=int)
    settings.smtp_username = request.form.get('smtp_username')
    settings.smtp_password = request.form.get('smtp_password')
    settings.smtp_use_tls = bool(request.form.get('smtp_use_tls'))
    settings.smtp_from_email = request.form.get('smtp_from_email')
    settings.smtp_from_name = request.form.get('smtp_from_name')
    
    settings.updated_by = current_user.id
    
    try:
        db.session.commit()
        flash('SMTP settings updated successfully!', 'success')
        logging.info(f"Admin {current_user.username} updated SMTP settings")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating SMTP settings: {str(e)}")
        flash('An error occurred.', 'error')
    
    return redirect(url_for('admin.settings'))

@admin_bp.route('/settings/smtp/test', methods=['POST'])
@login_required
@admin_required
def test_smtp():
    try:
        from utils.smtp_client import smtp_client
        
        # Test connection first
        connection_result = smtp_client.test_connection()
        
        if not connection_result['success']:
            return jsonify({
                'success': False,
                'message': connection_result['message']
            })
        
        # Send test email
        test_email_result = smtp_client.send_test_email(current_user.email)
        
        if test_email_result:
            message = f'SMTP test successful! Test email sent to {current_user.email}.'
            logging.info(f"Admin {current_user.username} successfully tested SMTP")
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': 'SMTP connection successful but failed to send test email.'
            })
            
    except Exception as e:
        logging.error(f"SMTP test failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'SMTP test failed: {str(e)}'
        })

@admin_bp.route('/database')
@login_required
@admin_required
def database_management():
    backups = DatabaseBackup.query.order_by(DatabaseBackup.created_at.desc()).all()
    
    # Get database statistics
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    stats = {
        'tables_count': len(tables),
        'users_count': User.query.count(),
        'tasks_count': Task.query.count(),
        'withdrawals_count': Withdrawal.query.count(),
        'airdrops_count': Airdrop.query.count(),
    }
    
    return render_template('admin/database.html', backups=backups, stats=stats)

@admin_bp.route('/database/export', methods=['POST'])
@login_required
@admin_required
def export_database():
    try:
        # Create backup record
        backup = DatabaseBackup(
            filename=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            backup_type='manual',
            created_by=current_user.id,
            status='in_progress'
        )
        db.session.add(backup)
        db.session.commit()
        
        # Export data
        export_data = {}
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        for table_name in tables:
            if table_name.startswith('alembic_'):
                continue
                
            result = db.session.execute(text(f'SELECT * FROM {table_name}'))
            columns = result.keys()
            rows = result.fetchall()
            
            export_data[table_name] = {
                'columns': list(columns),
                'data': [dict(zip(columns, row)) for row in rows]
            }
        
        # Save to file
        backup_dir = os.path.join(os.getcwd(), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_path = os.path.join(backup_dir, backup.filename)
        with open(backup_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        # Update backup record
        backup.status = 'completed'
        backup.file_size = os.path.getsize(backup_path)
        backup.tables_count = len(tables)
        backup.records_count = sum(len(table['data']) for table in export_data.values())
        
        db.session.commit()
        
        flash(f'Database exported successfully! File: {backup.filename}', 'success')
        logging.info(f"Admin {current_user.username} exported database")
        
    except Exception as e:
        if 'backup' in locals():
            backup.status = 'failed'
            backup.error_message = str(e)
            db.session.commit()
        
        logging.error(f"Database export failed: {str(e)}")
        flash(f'Database export failed: {str(e)}', 'error')
    
    return redirect(url_for('admin.database_management'))

@admin_bp.route('/database/download/<filename>')
@login_required
@admin_required
def download_backup(filename):
    """Download a database backup file"""
    backup_dir = os.path.join(os.getcwd(), 'backups')
    file_path = os.path.join(backup_dir, filename)
    
    if not os.path.exists(file_path):
        flash('Backup file not found.', 'error')
        return redirect(url_for('admin.database_management'))
    
    return send_file(file_path, as_attachment=True, download_name=filename)

@admin_bp.route('/database/import', methods=['POST'])
@login_required
@admin_required
def import_database():
    if 'backup_file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('admin.database_management'))
    
    file = request.files['backup_file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('admin.database_management'))
    
    try:
        # Read and parse JSON
        content = file.read().decode('utf-8')
        import_data = json.loads(content)
        
        # Clear existing data (be careful!)
        confirm = request.form.get('confirm_import')
        if confirm != 'yes':
            flash('Import cancelled. Please confirm by typing "yes".', 'error')
            return redirect(url_for('admin.database_management'))
        
        # Disable foreign key checks for SQLite
        if 'sqlite' in str(db.engine.url):
            db.session.execute(text('PRAGMA foreign_keys = OFF;'))
        else:
            db.session.execute(text('SET session_replication_role = replica;'))
        
        # Delete from tables (SQLite doesn't support TRUNCATE)
        for table_name in import_data.keys():
            if table_name.startswith('alembic_'):
                continue
            db.session.execute(text(f'DELETE FROM {table_name};'))
        
        # Import data
        for table_name, table_data in import_data.items():
            if table_name.startswith('alembic_'):
                continue
                
            for row in table_data['data']:
                columns = ', '.join([f'{key}' for key in row.keys()])
                placeholders = ', '.join([f":{key}" for key in row.keys()])
                query = text(f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})')
                db.session.execute(query, row)
        
        # Re-enable foreign key checks
        if 'sqlite' in str(db.engine.url):
            db.session.execute(text('PRAGMA foreign_keys = ON;'))
        else:
            db.session.execute(text('SET session_replication_role = DEFAULT;'))
        db.session.commit()
        
        flash('Database imported successfully!', 'success')
        logging.info(f"Admin {current_user.username} imported database")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Database import failed: {str(e)}")
        flash(f'Database import failed: {str(e)}', 'error')
    
    return redirect(url_for('admin.database_management'))

@admin_bp.route('/toggle_admin/<int:user_id>')
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent removing admin status from the only admin
    if user.is_admin and User.query.filter_by(is_admin=True).count() == 1:
        flash('Cannot remove admin status from the only admin user.', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = "granted admin privileges" if user.is_admin else "removed admin privileges"
    flash(f'User {user.username} has been {status}.', 'success')
    logging.info(f"Admin {current_user.username} {status} for user {user.username}")
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/verify_user_email/<int:user_id>')
@login_required
@admin_required
def verify_user_email(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.email_verified:
        flash(f'User {user.username} email is already verified.', 'info')
    else:
        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_expires = None
        
        try:
            db.session.commit()
            flash(f'User {user.username} email has been verified by admin.', 'success')
            logging.info(f"Admin {current_user.username} manually verified email for user {user.username}")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error verifying user email: {str(e)}")
            flash('An error occurred while verifying user email.', 'error')
    
    return redirect(url_for('admin.users'))

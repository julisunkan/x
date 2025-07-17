from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from models.task import Task, TaskCompletion
from models.referral import Referral, ReferralEarning, ReferralSettings
from utils.ai_verification import verify_task_proof
from utils.helpers import allowed_file, save_uploaded_file
from forms import TaskCompletionForm
import logging

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/')
@login_required
def tasks_page():
    # Get completed task IDs for current user
    completed_task_ids = [tc.task_id for tc in TaskCompletion.query.filter_by(user_id=current_user.id).all()]
    
    # Get available tasks (not completed by user and active)
    available_tasks = Task.query.filter(
        ~Task.id.in_(completed_task_ids),
        Task.is_active == True
    ).all()
    
    # Filter out tasks that have reached max completions
    available_tasks = [task for task in available_tasks if task.is_available]
    
    # Get user's task completions with status
    user_completions = TaskCompletion.query.filter_by(user_id=current_user.id).order_by(TaskCompletion.submitted_at.desc()).all()
    
    return render_template('tasks.html', 
                         available_tasks=available_tasks,
                         user_completions=user_completions)

@tasks_bp.route('/complete/<int:task_id>', methods=['GET', 'POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    form = TaskCompletionForm()
    
    # Check if task is available
    if not task.is_available:
        flash('This task is no longer available.', 'error')
        return redirect(url_for('tasks.tasks_page'))
    
    # Check if user already completed this task
    existing_completion = TaskCompletion.query.filter_by(
        user_id=current_user.id,
        task_id=task_id
    ).first()
    
    if existing_completion:
        flash('You have already completed this task.', 'error')
        return redirect(url_for('tasks.tasks_page'))
    
    if form.validate_on_submit():
        proof_text = form.proof_text.data.strip() if form.proof_text.data else ''
        proof_file = form.proof_file.data
        
        if task.requires_proof and not proof_text and not proof_file:
            flash('Proof is required for this task.', 'error')
            return render_template('tasks/complete.html', task=task, form=form)
        
        # Handle file upload
        proof_file_path = None
        if proof_file and proof_file.filename:
            if allowed_file(proof_file.filename):
                proof_file_path = save_uploaded_file(proof_file, 'task_proofs')
            else:
                flash('Invalid file type. Please upload an image.', 'error')
                return render_template('tasks/complete.html', task=task, form=form)
        
        # Create task completion
        completion = TaskCompletion(
            user_id=current_user.id,
            task_id=task_id,
            proof_text=proof_text,
            proof_file_path=proof_file_path
        )
        
        # AI verification if enabled
        if proof_text or proof_file_path:
            try:
                ai_score, ai_notes = verify_task_proof(task, proof_text, proof_file_path)
                completion.ai_verification_score = ai_score
                completion.ai_verification_notes = ai_notes
                
                # Auto-approve if AI score is high enough
                if ai_score and ai_score >= 0.8 and not task.requires_admin_approval:
                    completion.approve()
                    flash('Task completed and automatically approved!', 'success')
                else:
                    flash('Task submitted for review. You will be notified when it\'s approved.', 'info')
            except Exception as e:
                logging.error(f"AI verification error: {str(e)}")
                flash('Task submitted for manual review.', 'info')
        else:
            # Auto-approve tasks that don't require proof
            if not task.requires_proof:
                completion.approve()
                flash('Task completed!', 'success')
            else:
                flash('Task submitted for review.', 'info')
        
        db.session.add(completion)
        
        # Handle referral earnings for approved tasks
        if completion.status == 'approved' and current_user.referred_by:
            handle_referral_task_earning(completion)
        
        try:
            db.session.commit()
            logging.info(f"User {current_user.username} completed task {task.title}")
            return redirect(url_for('tasks.tasks_page'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Task completion error: {str(e)}")
            flash('An error occurred while submitting the task.', 'error')
    
    return render_template('tasks/complete.html', task=task, form=form)

@tasks_bp.route('/view/<int:completion_id>')
@login_required
def view_completion(completion_id):
    completion = TaskCompletion.query.get_or_404(completion_id)
    
    # Only allow user to view their own completions
    if completion.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('tasks.tasks_page'))
    
    return render_template('tasks/view_completion.html', completion=completion)

def handle_referral_task_earning(completion):
    """Handle referral earnings when a referred user completes a task"""
    referral = Referral.query.filter_by(
        referrer_id=current_user.referred_by,
        referred_id=current_user.id
    ).first()
    
    if referral and referral.is_active:
        settings = ReferralSettings.get_settings()
        referral_amount = completion.task.coin_reward * (settings.task_commission / 100)
        
        # Add to referrer's balance
        referrer = referral.referrer
        referrer.balance += referral_amount
        referral.earnings += referral_amount
        
        # Track the earning
        referral_earning = ReferralEarning(
            referral_id=referral.id,
            amount=referral_amount,
            earning_type='task_completion',
            description=f'Task completion commission from {current_user.username}: {completion.task.title}',
            related_task_completion_id=completion.id
        )
        db.session.add(referral_earning)

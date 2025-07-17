from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, TextAreaField, FloatField, IntegerField, SelectField, BooleanField, FileField, DateTimeLocalField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, URL, Optional
from flask_wtf.file import FileAllowed

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

class ForgotPasswordForm(FlaskForm):
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', 
                                   validators=[DataRequired(), EqualTo('password', message='Password does not match')])
    submit = SubmitField('Reset Password')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[Optional(), Length(max=64)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password', message='Password does not match')])
    profile_image = FileField('Profile Picture', validators=[
        DataRequired('Profile picture is required'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])
    referral_code = StringField('Referral Code (Optional)', validators=[Optional(), Length(max=16)])

class TaskCompletionForm(FlaskForm):
    proof_text = TextAreaField('Proof Description', validators=[Optional(), Length(max=1000)])
    proof_file = FileField('Proof Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])

class WithdrawalForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    withdrawal_method = SelectField('Withdrawal Method', choices=[
        ('paypal', 'PayPal'),
        ('bank', 'Bank Transfer'),
        ('crypto', 'Cryptocurrency')
    ], validators=[DataRequired()])
    payment_address = StringField('Payment Address/Email', validators=[DataRequired(), Length(max=200)])
    payment_details = TextAreaField('Additional Details', validators=[Optional(), Length(max=500)])

class TaskCreateForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    task_type = SelectField('Task Type', choices=[
        ('like', 'Like'),
        ('follow', 'Follow'),
        ('share', 'Share'),
        ('subscribe', 'Subscribe'),
        ('comment', 'Comment'),
        ('join', 'Join'),
        ('visit', 'Visit')
    ], validators=[DataRequired()])
    platform = SelectField('Platform', choices=[
        ('twitter', 'Twitter'),
        ('telegram', 'Telegram'),
        ('youtube', 'YouTube'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('discord', 'Discord'),
        ('tiktok', 'TikTok')
    ], validators=[DataRequired()])
    url = StringField('URL', validators=[DataRequired(), URL()])
    coin_reward = FloatField('Coin Reward', validators=[DataRequired(), NumberRange(min=0.01)])
    xp_reward = IntegerField('XP Reward', validators=[Optional(), NumberRange(min=0)])
    max_completions = IntegerField('Max Completions', validators=[Optional(), NumberRange(min=1)])
    requires_proof = BooleanField('Requires Proof')
    proof_instructions = TextAreaField('Proof Instructions', validators=[Optional(), Length(max=500)])
    requires_admin_approval = BooleanField('Requires Admin Approval', default=True)

class AirdropCreateForm(FlaskForm):
    title = StringField('Airdrop Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    total_coins = FloatField('Total Coins', validators=[DataRequired(), NumberRange(min=1)])
    coins_per_user = FloatField('Coins per User', validators=[DataRequired(), NumberRange(min=0.01)])
    max_participants = IntegerField('Max Participants', validators=[Optional(), NumberRange(min=1)])
    min_level = IntegerField('Minimum Level', validators=[Optional(), NumberRange(min=1)])
    min_balance = FloatField('Minimum Balance', validators=[Optional(), NumberRange(min=0)])
    min_referrals = IntegerField('Minimum Referrals', validators=[Optional(), NumberRange(min=0)])
    start_date = DateTimeLocalField('Start Date', validators=[DataRequired()])
    end_date = DateTimeLocalField('End Date', validators=[DataRequired()])

class ProfileUpdateForm(FlaskForm):
    first_name = StringField('First Name', validators=[Optional(), Length(max=64)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    profile_image = FileField('Profile Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', 
                                   validators=[DataRequired(), EqualTo('new_password')])

class AdminUserEditForm(FlaskForm):
    balance = FloatField('Balance', validators=[DataRequired(), NumberRange(min=0)])
    xp = IntegerField('XP', validators=[DataRequired(), NumberRange(min=0)])
    level = IntegerField('Level', validators=[DataRequired(), NumberRange(min=1)])
    is_active = BooleanField('Active')

class WithdrawalReviewForm(FlaskForm):
    action = SelectField('Action', choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject')
    ], validators=[DataRequired()])
    notes = TextAreaField('Admin Notes', validators=[Optional(), Length(max=500)])
    transaction_id = StringField('Transaction ID', validators=[Optional(), Length(max=100)])

class MiningEventForm(FlaskForm):
    name = StringField('Event Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    multiplier = FloatField('Multiplier', validators=[DataRequired(), NumberRange(min=0.1, max=10)])
    bonus_coins = FloatField('Bonus Coins', validators=[Optional(), NumberRange(min=0)])
    bonus_xp = IntegerField('Bonus XP', validators=[Optional(), NumberRange(min=0)])
    start_time = DateTimeLocalField('Start Time', validators=[DataRequired()])
    end_time = DateTimeLocalField('End Time', validators=[DataRequired()])

class DailyMissionForm(FlaskForm):
    name = StringField('Mission Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    mission_type = SelectField('Mission Type', choices=[
        ('mine', 'Mining'),
        ('tasks', 'Task Completions'),
        ('referrals', 'Referrals')
    ], validators=[DataRequired()])
    target_amount = IntegerField('Target Amount', validators=[DataRequired(), NumberRange(min=1)])
    coin_reward = FloatField('Coin Reward', validators=[DataRequired(), NumberRange(min=0)])
    xp_reward = IntegerField('XP Reward', validators=[Optional(), NumberRange(min=0)])

class SettingsForm(FlaskForm):
    # Withdrawal settings
    min_withdrawal_amount = FloatField('Min Withdrawal', validators=[DataRequired(), NumberRange(min=0.01)])
    max_withdrawal_amount = FloatField('Max Withdrawal', validators=[DataRequired(), NumberRange(min=1)])
    withdrawal_fee_percentage = FloatField('Fee %', validators=[DataRequired(), NumberRange(min=0, max=100)])
    withdrawal_fee_fixed = FloatField('Fixed Fee', validators=[DataRequired(), NumberRange(min=0)])
    withdrawals_enabled = BooleanField('Enable Withdrawals')
    
    # Referral settings
    signup_bonus = FloatField('Signup Bonus', validators=[DataRequired(), NumberRange(min=0)])
    mining_commission = FloatField('Mining Commission %', validators=[DataRequired(), NumberRange(min=0, max=100)])
    task_commission = FloatField('Task Commission %', validators=[DataRequired(), NumberRange(min=0, max=100)])
    referrals_enabled = BooleanField('Enable Referrals')

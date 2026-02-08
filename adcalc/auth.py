from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import db, User
import re
from flask import current_app

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def is_valid_email(email):
    """Simple email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Имя пользователя должно быть не менее 3 символов')
        
        if not email or not is_valid_email(email):
            errors.append('Введите корректный email')
        
        if not password or len(password) < 6:
            errors.append('Пароль должен быть не менее 6 символов')
        
        if password != password_confirm:
            errors.append('Пароли не совпадают')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            errors.append('Пользователь с таким именем уже существует')
        
        if User.query.filter_by(email=email).first():
            errors.append('Email уже зарегистрирован')
        
        # Enforce optional email whitelist if configured
        whitelist = None
        try:
            whitelist = current_app.config.get('EMAIL_WHITELIST')
        except Exception:
            errors.append('Пользователь не может быть зарегистрирован с данным email')
        if whitelist:
            allowed = [p.strip() for p in whitelist.split(',') if p.strip()]
            # Accept exact email matches or domain entries like @example.com
            def email_allowed(e):
                el = e.lower()
                for a in allowed:
                    a = a.lower()
                    if a.startswith('@'):
                        # domain match
                        if el.endswith(a):
                            return True
                    else:
                        if el == a:
                            return True
                return False

            if not email_allowed(email):
                errors.append('Регистрация по этому email запрещена')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login user"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Введите имя пользователя и пароль', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Добро пожаловать, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
            return render_template('auth/login.html')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('Вы вышли из аккаунта', 'info')
    return redirect(url_for('auth.login'))

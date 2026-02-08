# tests/test_auth.py
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adcalc import create_app
from adcalc.models import db, User


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
        'COST_PER_PERSON': 5
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


# -------- Registration Tests -------- #
def test_register_page_get(client):
    """GET /auth/register – show registration form"""
    rv = client.get('/auth/register')
    assert rv.status_code == 200
    assert 'Регистрация' in rv.data.decode('utf-8')
    assert 'Имя пользователя' in rv.data.decode('utf-8')


def test_register_success(client):
    """POST /auth/register – successfully register a new user"""
    rv = client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'password_confirm': 'password123'
    }, follow_redirects=True)
    
    assert rv.status_code == 200
    assert 'Регистрация успешна' in rv.data.decode('utf-8')
    
    # Verify user was created
    user = User.query.filter_by(username='testuser').first()
    assert user is not None
    assert user.email == 'test@example.com'
    assert user.check_password('password123')


def test_register_username_too_short(client):
    """POST /auth/register – reject username less than 3 chars"""
    rv = client.post('/auth/register', data={
        'username': 'ab',
        'email': 'test@example.com',
        'password': 'password123',
        'password_confirm': 'password123'
    })
    
    assert 'не менее 3 символов' in rv.data.decode('utf-8')
    assert User.query.count() == 0


def test_register_password_too_short(client):
    """POST /auth/register – reject password less than 6 chars"""
    rv = client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': '12345',
        'password_confirm': '12345'
    })
    
    assert 'не менее 6 символов' in rv.data.decode('utf-8')
    assert User.query.count() == 0



def test_register_duplicate_username(client):
    """POST /auth/register – reject duplicate username"""
    # Create first user
    user = User(username='testuser', email='test1@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    # Try to register with same username
    rv = client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'test2@example.com',
        'password': 'password123',
        'password_confirm': 'password123'
    })
    
    assert 'существует' in rv.data.decode('utf-8')
    assert User.query.count() == 1


def test_register_duplicate_email(client):
    """POST /auth/register – reject duplicate email"""
    # Create first user
    user = User(username='user1', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    # Try to register with same email
    rv = client.post('/auth/register', data={
        'username': 'user2',
        'email': 'test@example.com',
        'password': 'password123',
        'password_confirm': 'password123'
    })
    
    assert 'зарегистрирован' in rv.data.decode('utf-8')
    assert User.query.count() == 1


# -------- Login Tests -------- #
def test_login_page_get(client):
    """GET /auth/login – show login form"""
    rv = client.get('/auth/login')
    assert rv.status_code == 200
    assert 'Вход в систему' in rv.data.decode('utf-8')


def test_login_success(client):
    """POST /auth/login – successfully log in user"""
    # Create user
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    rv = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert rv.status_code == 200
    assert 'Калькулятор' in rv.data.decode('utf-8')


def test_login_invalid_username(client):
    """POST /auth/login – reject invalid username"""
    rv = client.post('/auth/login', data={
        'username': 'nonexistent',
        'password': 'password123'
    })
    
    assert 'Неверное имя пользователя' in rv.data.decode('utf-8')


def test_login_invalid_password(client):
    """POST /auth/login – reject invalid password"""
    # Create user
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    rv = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'wrongpassword'
    })
    
    assert 'Неверное имя пользователя или пароль' in rv.data.decode('utf-8')


def test_login_missing_fields(client):
    """POST /auth/login – reject missing credentials"""
    rv = client.post('/auth/login', data={
        'username': '',
        'password': ''
    })
    
    assert 'Введите имя пользователя' in rv.data.decode('utf-8')


# -------- Logout Tests -------- #
def test_logout(client):
    """GET /auth/logout – log out user and clear session"""
    # Create and login user
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    
    # Logout
    rv = client.get('/auth/logout', follow_redirects=True)
    assert rv.status_code == 200
    assert 'вышли из аккаунта' in rv.data.decode('utf-8')


# -------- Protected Routes Tests -------- #
def test_protected_route_redirects_to_login(client):
    """Protected routes should redirect to login when not authenticated"""
    rv = client.get('/broadcast/list')
    assert rv.status_code == 302
    assert '/auth/login' in rv.location


def test_protected_route_accessible_when_logged_in(client):
    """Protected routes should be accessible when authenticated"""
    # Create and login user
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    with client.session_transaction() as sess:
        sess['user_id'] = user.id
        sess['username'] = user.username
    
    rv = client.get('/broadcast/list')
    assert rv.status_code == 200


def test_protected_api_returns_401_when_not_authenticated(client):
    """Protected API endpoints should return 401 when not authenticated"""
    rv = client.get('/api/organisations-detailed')
    assert rv.status_code == 401
    data = rv.get_json()
    assert 'error' in data


def test_protected_api_accessible_when_authenticated(client):
    """Protected API endpoints should work when authenticated"""
    # Create and login user
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    with client.session_transaction() as sess:
        sess['user_id'] = user.id
        sess['username'] = user.username
    
    rv = client.get('/api/organisations-detailed')
    assert rv.status_code == 200


# -------- Email whitelist tests -------- #
def test_register_with_whitelist_exact_allowed(client):
    """Registration allowed when EMAIL_WHITELIST contains exact email"""
    client.application.config['EMAIL_WHITELIST'] = 'allowed@example.com'
    rv = client.post('/auth/register', data={
        'username': 'alloweduser',
        'email': 'allowed@example.com',
        'password': 'password123',
        'password_confirm': 'password123'
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert 'Регистрация успешна' in rv.data.decode('utf-8')
    # User created
    u = User.query.filter_by(username='alloweduser').first()
    assert u is not None


def test_register_with_whitelist_domain_allowed(client):
    """Registration allowed when EMAIL_WHITELIST contains domain like @example.org"""
    client.application.config['EMAIL_WHITELIST'] = '@example.org'
    rv = client.post('/auth/register', data={
        'username': 'domainuser',
        'email': 'person@example.org',
        'password': 'password123',
        'password_confirm': 'password123'
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert 'Регистрация успешна' in rv.data.decode('utf-8')
    u = User.query.filter_by(username='domainuser').first()
    assert u is not None


def test_register_with_whitelist_disallowed(client):
    """Registration rejected when email not in whitelist"""
    client.application.config['EMAIL_WHITELIST'] = 'allowed@example.com,@example.org'
    rv = client.post('/auth/register', data={
        'username': 'baduser',
        'email': 'bad@other.com',
        'password': 'password123',
        'password_confirm': 'password123'
    })
    assert rv.status_code == 200
    # Should show error message about whitelist
    assert 'Регистрация по этому email запрещена' in rv.data.decode('utf-8')
    assert User.query.filter_by(username='baduser').first() is None

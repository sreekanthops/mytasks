from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database configuration - supports both PostgreSQL and SQLite
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///mytasks.db')
# Handle Heroku postgres:// to postgresql:// conversion
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

db = SQLAlchemy(app)

# Database Models
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, inprogress, done, hold, archive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = db.Column(db.DateTime)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    reminder_time = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DashboardLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    environment_id = db.Column(db.Integer, db.ForeignKey('environment.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Environment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(20), default='#2563eb')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    links = db.relationship('DashboardLink', backref='environment', lazy=True)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    github_token = db.Column(db.String(200))
    github_username = db.Column(db.String(100))

# Routes
@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/github/issues')
def get_github_issues():
    status = request.args.get('status', 'open')
    settings = Settings.query.first()
    
    if not settings or not settings.github_token:
        return jsonify({'error': 'GitHub token not configured'}), 400
    
    headers = {
        'Authorization': f'token {settings.github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # For IBM GitHub Enterprise - correct API endpoint
    url = 'https://github.ibm.com/api/v3/repos/nettools/road-map/issues'
    params = {
        'state': status,
        'assignee': settings.github_username or 'Sreekanth-Chityala'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, verify=True)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            error_msg = f'GitHub API error: {response.status_code}'
            try:
                error_detail = response.json()
                error_msg += f' - {error_detail.get("message", "")}'
            except:
                error_msg += f' - {response.text[:200]}'
            return jsonify({'error': error_msg}), response.status_code
    except Exception as e:
        return jsonify({'error': f'Connection error: {str(e)}'}), 500

@app.route('/api/tasks', methods=['GET', 'POST'])
def tasks():
    if request.method == 'POST':
        data = request.json
        task = Task(
            title=data['title'],
            description=data.get('description', ''),
            status=data.get('status', 'pending'),
            due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None
        )
        db.session.add(task)
        db.session.commit()
        return jsonify({'id': task.id, 'message': 'Task created successfully'})
    
    status = request.args.get('status')
    query = Task.query
    if status:
        query = query.filter_by(status=status)
    tasks = query.order_by(Task.created_at.desc()).all()
    
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'description': t.description,
        'status': t.status,
        'created_at': t.created_at.isoformat(),
        'updated_at': t.updated_at.isoformat(),
        'due_date': t.due_date.isoformat() if t.due_date else None
    } for t in tasks])

@app.route('/api/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'PUT':
        data = request.json
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        task.status = data.get('status', task.status)
        if data.get('due_date'):
            task.due_date = datetime.fromisoformat(data['due_date'])
        db.session.commit()
        return jsonify({'message': 'Task updated successfully'})
    
    elif request.method == 'DELETE':
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'})

@app.route('/api/reminders', methods=['GET', 'POST'])
def reminders():
    if request.method == 'POST':
        data = request.json
        reminder = Reminder(
            title=data['title'],
            description=data.get('description', ''),
            reminder_time=datetime.fromisoformat(data['reminder_time'])
        )
        db.session.add(reminder)
        db.session.commit()
        return jsonify({'id': reminder.id, 'message': 'Reminder created successfully'})
    
    reminders = Reminder.query.filter_by(is_active=True).order_by(Reminder.reminder_time).all()
    return jsonify([{
        'id': r.id,
        'title': r.title,
        'description': r.description,
        'reminder_time': r.reminder_time.isoformat(),
        'created_at': r.created_at.isoformat()
    } for r in reminders])

@app.route('/api/reminders/<int:reminder_id>', methods=['DELETE'])
def reminder_detail(reminder_id):
    reminder = Reminder.query.get_or_404(reminder_id)
    reminder.is_active = False
    db.session.commit()
    return jsonify({'message': 'Reminder dismissed'})

@app.route('/api/links', methods=['GET', 'POST'])
def links():
    if request.method == 'POST':
        data = request.json
        link = DashboardLink(
            name=data['name'],
            url=data['url'],
            description=data.get('description', ''),
            environment_id=data.get('environment_id')
        )
        db.session.add(link)
        db.session.commit()
        return jsonify({'id': link.id, 'message': 'Link created successfully'})
    
    search = request.args.get('search', '')
    env_id = request.args.get('environment_id')
    
    query = DashboardLink.query
    if search:
        query = query.filter(DashboardLink.name.ilike(f'%{search}%'))
    if env_id:
        query = query.filter_by(environment_id=int(env_id))
    
    links = query.order_by(DashboardLink.name).all()
    
    return jsonify([{
        'id': l.id,
        'name': l.name,
        'url': l.url,
        'description': l.description,
        'environment_id': l.environment_id,
        'environment': l.environment.name if l.environment else None,
        'environment_color': l.environment.color if l.environment else None,
        'created_at': l.created_at.isoformat()
    } for l in links])

@app.route('/api/links/<int:link_id>', methods=['DELETE'])
def link_detail(link_id):
    link = DashboardLink.query.get_or_404(link_id)
    db.session.delete(link)
    db.session.commit()
    return jsonify({'message': 'Link deleted successfully'})

@app.route('/api/environments', methods=['GET', 'POST'])
def environments():
    if request.method == 'POST':
        data = request.json
        env = Environment(
            name=data['name'],
            color=data.get('color', '#2563eb')
        )
        db.session.add(env)
        db.session.commit()
        return jsonify({'id': env.id, 'message': 'Environment created successfully'})
    
    environments = Environment.query.order_by(Environment.name).all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'color': e.color,
        'link_count': len(e.links)
    } for e in environments])

@app.route('/api/environments/<int:env_id>', methods=['DELETE'])
def environment_detail(env_id):
    env = Environment.query.get_or_404(env_id)
    db.session.delete(env)
    db.session.commit()
    return jsonify({'message': 'Environment deleted successfully'})

@app.route('/api/tasks/from-github/<int:issue_number>', methods=['POST'])
def create_task_from_github(issue_number):
    settings = Settings.query.first()
    
    if not settings or not settings.github_token:
        return jsonify({'error': 'GitHub token not configured'}), 400
    
    headers = {
        'Authorization': f'token {settings.github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = f'https://github.ibm.com/api/v3/repos/nettools/road-map/issues/{issue_number}'
    
    try:
        response = requests.get(url, headers=headers, verify=True)
        if response.status_code == 200:
            issue = response.json()
            task = Task(
                title=f"#{issue['number']} {issue['title']}",
                description=issue.get('body', ''),
                status='pending'
            )
            db.session.add(task)
            db.session.commit()
            return jsonify({'id': task.id, 'message': 'Task created from GitHub issue'})
        else:
            return jsonify({'error': f'GitHub API error: {response.status_code}'}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        data = request.json
        settings = Settings.query.first()
        if not settings:
            settings = Settings()
            db.session.add(settings)
        
        settings.github_token = data.get('github_token', settings.github_token)
        settings.github_username = data.get('github_username', settings.github_username)
        db.session.commit()
        return jsonify({'message': 'Settings saved successfully'})
    
    settings = Settings.query.first()
    if settings:
        return jsonify({
            'github_username': settings.github_username,
            'has_token': bool(settings.github_token)
        })
    return jsonify({'github_username': '', 'has_token': False})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Get host and port from environment or use defaults
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    app.run(host=host, port=port, debug=debug)

# Made with Bob

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os
import json
import subprocess
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
    github_issue_number = db.Column(db.String(50))  # GitHub issue number
    github_issue_title = db.Column(db.String(500))  # GitHub issue title
    github_issue_url = db.Column(db.String(500))  # GitHub issue URL
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    deadline = db.Column(db.DateTime)  # Task deadline
    is_muted = db.Column(db.Boolean, default=False)  # Mute deadline reminders
    mute_until = db.Column(db.DateTime)  # Mute until specific time (snooze)
    last_reminded_at = db.Column(db.DateTime)  # Last reminder time
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    task_reminders = db.relationship('TaskReminder', backref='task', lazy=True, cascade='all, delete-orphan')

class TaskReminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    reminder_type = db.Column(db.String(20), nullable=False)  # before_deadline, daily, custom
    interval_minutes = db.Column(db.Integer)  # 15, 30, 60, 180, or custom
    custom_time = db.Column(db.DateTime)  # For custom reminders
    is_active = db.Column(db.Boolean, default=True)
    last_triggered = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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
    jira_url = db.Column(db.String(200))  # e.g., https://your-domain.atlassian.net
    jira_email = db.Column(db.String(200))  # Email for Jira authentication
    jira_api_token = db.Column(db.String(200))  # API token from Atlassian
    jira_project_key = db.Column(db.String(50))  # Default project key (e.g., PROJ)

# Routes
@app.route('/')
def index():
    return redirect(url_for('github_page'))

@app.route('/github')
def github_page():
    return render_template('github.html', active_page='github')

@app.route('/jira')
def jira_page():
    return render_template('jira.html', active_page='jira')

@app.route('/tasks')
def tasks_page():
    return render_template('tasks.html', active_page='tasks')

@app.route('/reminders')
def reminders_page():
    return render_template('reminders.html', active_page='reminders')

@app.route('/links')
def links_page():
    return render_template('links.html', active_page='links')

@app.route('/settings')
def settings_page():
    return render_template('settings.html', active_page='settings')

@app.route('/fcp')
def fcp_page():
    """FCP Manager - redirect to wizard"""
    return redirect(url_for('fcp_wizard'))

@app.route('/fcp/old')
def fcp_page_old():
    """Old FCP Manager page (modal-based)"""
    return render_template('fcp.html', active_page='fcp')

# Keep old dashboard route for backward compatibility
@app.route('/dashboard')
def dashboard():
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
            github_issue_number=data.get('github_issue_number'),
            github_issue_title=data.get('github_issue_title'),
            github_issue_url=data.get('github_issue_url'),
            priority=data.get('priority', 'medium'),
            deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None,
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
        'github_issue_number': t.github_issue_number,
        'github_issue_title': t.github_issue_title,
        'github_issue_url': t.github_issue_url,
        'priority': t.priority,
        'deadline': t.deadline.isoformat() if t.deadline else None,
        'is_muted': t.is_muted,
        'mute_until': t.mute_until.isoformat() if t.mute_until else None,
        'reminder_count': len(t.task_reminders),
        'created_at': t.created_at.isoformat(),
        'updated_at': t.updated_at.isoformat(),
        'due_date': t.due_date.isoformat() if t.due_date else None
    } for t in tasks])

@app.route('/api/tasks/<int:task_id>', methods=['GET', 'PUT', 'DELETE'])
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'github_issue_number': task.github_issue_number,
            'github_issue_title': task.github_issue_title,
            'github_issue_url': task.github_issue_url,
            'priority': task.priority,
            'deadline': task.deadline.isoformat() if task.deadline else None,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'is_muted': task.is_muted,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat()
        })
    
    elif request.method == 'PUT':
        data = request.json
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        task.status = data.get('status', task.status)
        task.priority = data.get('priority', task.priority)
        
        # Handle deadline
        if 'deadline' in data:
            task.deadline = datetime.fromisoformat(data['deadline']) if data['deadline'] else None
        
        # Handle due_date
        if 'due_date' in data:
            task.due_date = datetime.fromisoformat(data['due_date']) if data['due_date'] else None
        
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

@app.route('/api/links/<int:link_id>', methods=['GET', 'PUT', 'DELETE'])
def link_detail(link_id):
    link = DashboardLink.query.get_or_404(link_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': link.id,
            'name': link.name,
            'url': link.url,
            'description': link.description,
            'environment_id': link.environment_id,
            'created_at': link.created_at.isoformat()
        })
    
    elif request.method == 'PUT':
        data = request.json
        link.name = data.get('name', link.name)
        link.url = data.get('url', link.url)
        link.description = data.get('description', link.description)
        link.environment_id = data.get('environment_id')
        db.session.commit()
        return jsonify({'message': 'Link updated successfully'})
    
    elif request.method == 'DELETE':
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
        settings.jira_url = data.get('jira_url', settings.jira_url)
        settings.jira_email = data.get('jira_email', settings.jira_email)
        settings.jira_api_token = data.get('jira_api_token', settings.jira_api_token)
        settings.jira_project_key = data.get('jira_project_key', settings.jira_project_key)
        db.session.commit()
        return jsonify({'message': 'Settings saved successfully'})
    
    settings = Settings.query.first()
    if settings:
        return jsonify({
            'github_username': settings.github_username,
            'has_token': bool(settings.github_token),
            'jira_url': settings.jira_url,
            'jira_email': settings.jira_email,
            'has_jira_token': bool(settings.jira_api_token),
            'jira_project_key': settings.jira_project_key
        })
    return jsonify({
        'github_username': '',
        'has_token': False,
        'jira_url': '',
        'jira_email': '',
        'has_jira_token': False,
        'jira_project_key': ''
    })

@app.route('/api/jira/issues')
def get_jira_issues():
    """Get Jira issues assigned to the user"""
    status = request.args.get('status', 'open')  # open, in_progress, done
    settings = Settings.query.first()
    
    if not settings or not settings.jira_api_token or not settings.jira_url:
        return jsonify({'error': 'Jira not configured. Please configure in Settings.'}), 400
    
    # Map status to Jira status names
    status_map = {
        'open': ['To Do', 'Open', 'Backlog'],
        'in_progress': ['In Progress', 'In Review'],
        'done': ['Done', 'Closed', 'Resolved']
    }
    
    jira_statuses = status_map.get(status, ['To Do', 'Open'])
    
    # Build JQL query
    jql_parts = []
    if settings.jira_email:
        jql_parts.append(f'assignee = "{settings.jira_email}"')
    if settings.jira_project_key:
        jql_parts.append(f'project = "{settings.jira_project_key}"')
    
    # Add status filter
    status_filter = ' OR '.join([f'status = "{s}"' for s in jira_statuses])
    jql_parts.append(f'({status_filter})')
    
    jql = ' AND '.join(jql_parts)
    jql += ' ORDER BY updated DESC'
    
    # Jira REST API endpoint - using the new /search/jql endpoint
    url = f'{settings.jira_url.rstrip("/")}/rest/api/3/search/jql'
    
    # Basic auth with email and API token
    from base64 import b64encode
    credentials = b64encode(f'{settings.jira_email}:{settings.jira_api_token}'.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {credentials}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    params = {
        'jql': jql,
        'maxResults': 50,
        'fields': 'summary,status,priority,assignee,created,updated,description,issuetype'
    }
    
    try:
        print(f"DEBUG: Jira URL: {url}")
        print(f"DEBUG: JQL Query: {jql}")
        print(f"DEBUG: Email: {settings.jira_email}")
        
        response = requests.get(url, headers=headers, params=params, verify=True, timeout=10)
        
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response headers: {response.headers.get('content-type')}")
        
        if response.status_code == 200:
            data = response.json()
            issues = []
            for issue in data.get('issues', []):
                fields = issue.get('fields', {})
                issues.append({
                    'key': issue.get('key'),
                    'id': issue.get('id'),
                    'summary': fields.get('summary'),
                    'description': fields.get('description', {}).get('content', [{}])[0].get('content', [{}])[0].get('text', '') if isinstance(fields.get('description'), dict) else '',
                    'status': fields.get('status', {}).get('name'),
                    'priority': fields.get('priority', {}).get('name', 'Medium'),
                    'type': fields.get('issuetype', {}).get('name'),
                    'created': fields.get('created'),
                    'updated': fields.get('updated'),
                    'url': f"{settings.jira_url.rstrip('/')}/browse/{issue.get('key')}"
                })
            return jsonify(issues)
        else:
            error_msg = f'Jira API error: {response.status_code}'
            try:
                error_detail = response.json()
                error_msg += f' - {error_detail.get("errorMessages", ["Unknown error"])[0]}'
            except:
                error_msg += f' - {response.text[:200]}'
            print(f"DEBUG: Error response: {error_msg}")
            return jsonify({'error': error_msg}), response.status_code
    except requests.exceptions.JSONDecodeError as e:
        error_msg = f'Invalid JSON response from Jira. Check your Jira URL and credentials. Response: {response.text[:200]}'
        print(f"DEBUG: JSON decode error: {error_msg}")
        return jsonify({'error': error_msg}), 500
    except requests.exceptions.RequestException as e:
        error_msg = f'Connection error: {str(e)}. Check your Jira URL and network connection.'
        print(f"DEBUG: Request exception: {error_msg}")
        return jsonify({'error': error_msg}), 500
    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        print(f"DEBUG: Unexpected error: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

@app.route('/api/tasks/from-jira/<string:issue_key>', methods=['POST'])
def create_task_from_jira(issue_key):
    """Create a task from a Jira issue"""
    settings = Settings.query.first()
    
    if not settings or not settings.jira_api_token or not settings.jira_url:
        return jsonify({'error': 'Jira not configured'}), 400
    
    # Get issue details from Jira
    url = f'{settings.jira_url.rstrip("/")}/rest/api/3/issue/{issue_key}'
    
    from base64 import b64encode
    credentials = b64encode(f'{settings.jira_email}:{settings.jira_api_token}'.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {credentials}',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, verify=True)
        if response.status_code == 200:
            issue = response.json()
            fields = issue.get('fields', {})
            
            # Extract description text
            description = ''
            desc_data = fields.get('description', {})
            if isinstance(desc_data, dict) and 'content' in desc_data:
                for content_block in desc_data.get('content', []):
                    if content_block.get('type') == 'paragraph':
                        for text_item in content_block.get('content', []):
                            if text_item.get('type') == 'text':
                                description += text_item.get('text', '') + '\n'
            
            task = Task(
                title=f"[{issue_key}] {fields.get('summary', '')}",
                description=description.strip(),
                status='pending',
                github_issue_number=issue_key,
                github_issue_url=f"{settings.jira_url.rstrip('/')}/browse/{issue_key}",
                priority=fields.get('priority', {}).get('name', 'Medium').lower()
            )
            db.session.add(task)
            db.session.commit()
            return jsonify({'id': task.id, 'message': 'Task created from Jira issue'})
        else:
            return jsonify({'error': f'Jira API error: {response.status_code}'}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/mute', methods=['POST'])
def mute_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.is_muted = not task.is_muted
    db.session.commit()
    return jsonify({'message': 'Task muted' if task.is_muted else 'Task unmuted', 'is_muted': task.is_muted})

@app.route('/api/tasks/<int:task_id>/snooze', methods=['POST'])
def snooze_task(task_id):
    """Snooze task urgency for a specific duration"""
    task = Task.query.get_or_404(task_id)
    data = request.json
    
    minutes = data.get('minutes')
    custom_time = data.get('custom_time')
    
    from datetime import timedelta
    now = datetime.utcnow()
    
    if custom_time:
        # Custom snooze time
        try:
            custom_time = custom_time.replace('Z', '+00:00')
            task.mute_until = datetime.fromisoformat(custom_time)
        except ValueError as e:
            return jsonify({'error': f'Invalid time format: {str(e)}'}), 400
    elif minutes:
        # Snooze for specific minutes
        task.mute_until = now + timedelta(minutes=int(minutes))
    else:
        return jsonify({'error': 'Either minutes or custom_time is required'}), 400
    
    db.session.commit()
    return jsonify({
        'message': f'Task snoozed until {task.mute_until.isoformat()}',
        'mute_until': task.mute_until.isoformat()
    })

@app.route('/api/tasks/<int:task_id>/unsnooze', methods=['POST'])
def unsnooze_task(task_id):
    """Remove snooze from task"""
    task = Task.query.get_or_404(task_id)
    task.mute_until = None
    db.session.commit()
    return jsonify({'message': 'Task unsnoo zed'})

@app.route('/api/tasks/urgent-count', methods=['GET'])
def get_urgent_count():
    """Get count of urgent tasks (not snoozed)"""
    from datetime import timedelta
    now = datetime.utcnow()
    one_day_from_now = now + timedelta(days=1)
    
    # Get tasks with deadline < 24 hours, not completed/archived, and not snoozed
    urgent_tasks = Task.query.filter(
        Task.deadline.isnot(None),
        Task.deadline <= one_day_from_now,
        Task.status.notin_(['done', 'archive']),
        db.or_(
            Task.mute_until.is_(None),
            Task.mute_until <= now
        )
    ).all()
    
    return jsonify({'count': len(urgent_tasks)})

@app.route('/api/deadline-reminders')
def get_deadline_reminders():
    """Check for tasks with approaching deadlines"""
    from datetime import timedelta
    
    now = datetime.utcnow()
    one_week = now + timedelta(days=7)
    one_day = now + timedelta(days=1)
    three_hours = timedelta(hours=3)
    
    # Get all non-completed, non-muted tasks with deadlines
    tasks = Task.query.filter(
        Task.deadline.isnot(None),
        Task.status.notin_(['done', 'archive']),
        Task.is_muted == False
    ).all()
    
    reminders = []
    
    for task in tasks:
        if task.deadline <= now:
            # Overdue - remind every 3 hours
            if not task.last_reminded_at or (now - task.last_reminded_at) >= three_hours:
                reminders.append({
                    'id': task.id,
                    'title': task.title,
                    'deadline': task.deadline.isoformat(),
                    'urgency': 'overdue',
                    'message': f'⚠️ OVERDUE: {task.title}',
                    'github_issue_number': task.github_issue_number,
                    'github_issue_url': task.github_issue_url
                })
                task.last_reminded_at = now
        elif task.deadline <= one_day:
            # Within 1 day - remind every 3 hours
            if not task.last_reminded_at or (now - task.last_reminded_at) >= three_hours:
                reminders.append({
                    'id': task.id,
                    'title': task.title,
                    'deadline': task.deadline.isoformat(),
                    'urgency': 'critical',
                    'message': f'🔴 Due in less than 24 hours: {task.title}',
                    'github_issue_number': task.github_issue_number,
                    'github_issue_url': task.github_issue_url
                })
                task.last_reminded_at = now
        elif task.deadline <= one_week:
            # Within 1 week - remind once daily
            if not task.last_reminded_at or (now - task.last_reminded_at) >= timedelta(days=1):
                reminders.append({
                    'id': task.id,
                    'title': task.title,
                    'deadline': task.deadline.isoformat(),
                    'urgency': 'warning',
                    'message': f'🟡 Due within a week: {task.title}',
                    'github_issue_number': task.github_issue_number,
                    'github_issue_url': task.github_issue_url
                })
                task.last_reminded_at = now
    
    if reminders:
        db.session.commit()
    
    return jsonify(reminders)


# Task Reminder Management Endpoints
@app.route('/api/task-reminders/<int:task_id>', methods=['GET'])
def get_task_reminders(task_id):
    """Get all reminders for a specific task"""
    task = Task.query.get_or_404(task_id)
    reminders = TaskReminder.query.filter_by(task_id=task_id).all()
    return jsonify([{
        'id': r.id,
        'reminder_type': r.reminder_type,
        'interval_minutes': r.interval_minutes,
        'custom_time': r.custom_time.isoformat() if r.custom_time else None,
        'is_active': r.is_active,
        'last_triggered': r.last_triggered.isoformat() if r.last_triggered else None,
        'created_at': r.created_at.isoformat() if r.created_at else None
    } for r in reminders])

@app.route('/api/task-reminders', methods=['POST'])
def create_task_reminder():
    """Create a new task reminder"""
    data = request.json
    print(f"DEBUG: Received data: {data}")  # Debug logging
    
    task_id = data.get('task_id')
    if not task_id:
        return jsonify({'error': 'task_id is required'}), 400
    
    task = Task.query.get_or_404(task_id)
    
    # Validate reminder type
    reminder_type = data.get('reminder_type')
    if reminder_type not in ['before_deadline', 'daily', 'custom']:
        return jsonify({'error': 'Invalid reminder_type. Must be: before_deadline, daily, or custom'}), 400
    
    # Validate based on reminder type
    if reminder_type == 'before_deadline':
        if not task.deadline:
            return jsonify({'error': 'Task must have a deadline for before_deadline reminders'}), 400
        interval_minutes = data.get('interval_minutes')
        if not interval_minutes or interval_minutes not in [15, 30, 60, 180]:
            return jsonify({'error': 'interval_minutes must be 15, 30, 60, or 180 for before_deadline reminders'}), 400
        
        reminder = TaskReminder(
            task_id=task_id,
            reminder_type=reminder_type,
            interval_minutes=interval_minutes
        )
    
    elif reminder_type == 'daily':
        # Daily reminder at a specific time
        custom_time_str = data.get('custom_time')
        if not custom_time_str:
            return jsonify({'error': 'custom_time is required for daily reminders'}), 400
        
        try:
            # Handle JavaScript's toISOString() format with Z suffix
            custom_time_str = custom_time_str.replace('Z', '+00:00')
            custom_time = datetime.fromisoformat(custom_time_str)
        except ValueError as e:
            return jsonify({'error': f'Invalid custom_time format: {str(e)}'}), 400
        
        reminder = TaskReminder(
            task_id=task_id,
            reminder_type=reminder_type,
            custom_time=custom_time
        )
    
    elif reminder_type == 'custom':
        # One-time custom reminder
        custom_time_str = data.get('custom_time')
        if not custom_time_str:
            return jsonify({'error': 'custom_time is required for custom reminders'}), 400
        
        try:
            # Handle JavaScript's toISOString() format with Z suffix
            custom_time_str = custom_time_str.replace('Z', '+00:00')
            custom_time = datetime.fromisoformat(custom_time_str)
        except ValueError as e:
            return jsonify({'error': f'Invalid custom_time format: {str(e)}'}), 400
        
        reminder = TaskReminder(
            task_id=task_id,
            reminder_type=reminder_type,
            custom_time=custom_time
        )
    
    db.session.add(reminder)
    db.session.commit()
    
    return jsonify({
        'id': reminder.id,
        'reminder_type': reminder.reminder_type,
        'interval_minutes': reminder.interval_minutes,
        'custom_time': reminder.custom_time.isoformat() if reminder.custom_time else None,
        'is_active': reminder.is_active,
        'created_at': reminder.created_at.isoformat() if reminder.created_at else None
    }), 201

@app.route('/api/task-reminders/<int:reminder_id>', methods=['DELETE', 'PATCH'])
def manage_single_task_reminder(reminder_id):
    """Delete or update a specific task reminder"""
    reminder = TaskReminder.query.get_or_404(reminder_id)
    
    if request.method == 'DELETE':
        db.session.delete(reminder)
        db.session.commit()
        return jsonify({'message': 'Reminder deleted successfully'})
    
    elif request.method == 'PATCH':
        # Toggle active status
        data = request.json
        if 'is_active' in data:
            reminder.is_active = data['is_active']
            db.session.commit()
        
        return jsonify({
            'id': reminder.id,
            'reminder_type': reminder.reminder_type,
            'interval_minutes': reminder.interval_minutes,
            'custom_time': reminder.custom_time.isoformat() if reminder.custom_time else None,
            'is_active': reminder.is_active,
            'last_triggered': reminder.last_triggered.isoformat() if reminder.last_triggered else None
        })

# Keep old endpoint for backward compatibility
@app.route('/api/tasks/<int:task_id>/reminders', methods=['GET', 'POST'])
def manage_task_reminders(task_id):
    """Get or create reminders for a specific task (legacy endpoint)"""
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'GET':
        # Get all reminders for this task
        reminders = TaskReminder.query.filter_by(task_id=task_id).all()
        return jsonify([{
            'id': r.id,
            'reminder_type': r.reminder_type,
            'interval_minutes': r.interval_minutes,
            'custom_time': r.custom_time.isoformat() if r.custom_time else None,
            'is_active': r.is_active,
            'last_triggered': r.last_triggered.isoformat() if r.last_triggered else None,
            'created_at': r.created_at.isoformat() if r.created_at else None
        } for r in reminders])
    
    elif request.method == 'POST':
        # Create a new reminder for this task
        data = request.json
        print(f"DEBUG: Received data: {data}")  # Debug logging
        
        # Validate reminder type
        reminder_type = data.get('reminder_type')
        if reminder_type not in ['before_deadline', 'daily', 'custom']:
            return jsonify({'error': 'Invalid reminder_type. Must be: before_deadline, daily, or custom'}), 400
        
        # Validate based on reminder type
        if reminder_type == 'before_deadline':
            if not task.deadline:
                return jsonify({'error': 'Task must have a deadline for before_deadline reminders'}), 400
            interval_minutes = data.get('interval_minutes')
            if not interval_minutes or interval_minutes not in [15, 30, 60, 180]:
                return jsonify({'error': 'interval_minutes must be 15, 30, 60, or 180 for before_deadline reminders'}), 400
            
            reminder = TaskReminder(
                task_id=task_id,
                reminder_type=reminder_type,
                interval_minutes=interval_minutes
            )
        
        elif reminder_type == 'daily':
            # Daily reminder at a specific time
            custom_time_str = data.get('custom_time')
            if not custom_time_str:
                return jsonify({'error': 'custom_time is required for daily reminders'}), 400
            
            try:
                # Handle JavaScript's toISOString() format with Z suffix
                custom_time_str = custom_time_str.replace('Z', '+00:00')
                custom_time = datetime.fromisoformat(custom_time_str)
            except ValueError as e:
                return jsonify({'error': f'Invalid custom_time format: {str(e)}'}), 400
            
            reminder = TaskReminder(
                task_id=task_id,
                reminder_type=reminder_type,
                custom_time=custom_time
            )
        
        elif reminder_type == 'custom':
            # One-time custom reminder
            custom_time_str = data.get('custom_time')
            if not custom_time_str:
                return jsonify({'error': 'custom_time is required for custom reminders'}), 400
            
            try:
                # Handle JavaScript's toISOString() format with Z suffix
                custom_time_str = custom_time_str.replace('Z', '+00:00')
                custom_time = datetime.fromisoformat(custom_time_str)
            except ValueError as e:
                return jsonify({'error': f'Invalid custom_time format: {str(e)}'}), 400
            
            reminder = TaskReminder(
                task_id=task_id,
                reminder_type=reminder_type,
                custom_time=custom_time
            )
        
        db.session.add(reminder)
        db.session.commit()
        
        return jsonify({
            'id': reminder.id,
            'reminder_type': reminder.reminder_type,
            'interval_minutes': reminder.interval_minutes,
            'custom_time': reminder.custom_time.isoformat() if reminder.custom_time else None,
            'is_active': reminder.is_active,
            'created_at': reminder.created_at.isoformat() if reminder.created_at else None
        }), 201


@app.route('/api/tasks/<int:task_id>/reminders/<int:reminder_id>', methods=['DELETE', 'PATCH'])
def manage_single_reminder(task_id, reminder_id):
    """Delete or update a specific reminder"""
    reminder = TaskReminder.query.filter_by(id=reminder_id, task_id=task_id).first_or_404()
    
    if request.method == 'DELETE':
        db.session.delete(reminder)
        db.session.commit()
        return jsonify({'message': 'Reminder deleted successfully'})
    
    elif request.method == 'PATCH':
        # Toggle active status
        data = request.json
        if 'is_active' in data:
            reminder.is_active = data['is_active']
            db.session.commit()
        
        return jsonify({
            'id': reminder.id,
            'reminder_type': reminder.reminder_type,
            'interval_minutes': reminder.interval_minutes,
            'custom_time': reminder.custom_time.isoformat() if reminder.custom_time else None,
            'is_active': reminder.is_active,
            'last_triggered': reminder.last_triggered.isoformat() if reminder.last_triggered else None
        })


@app.route('/api/task-reminders/check')
def check_task_reminders():
    """Check and return due task reminders"""
    from datetime import timedelta
    
    now = datetime.utcnow()
    due_reminders = []
    
    # Get all active reminders
    reminders = TaskReminder.query.filter_by(is_active=True).all()
    
    for reminder in reminders:
        task = reminder.task
        
        # Skip if task is completed, archived, or muted
        if task.status in ['done', 'archive'] or task.is_muted:
            continue
        
        should_remind = False
        reminder_message = ""
        
        if reminder.reminder_type == 'before_deadline':
            # Check if we should remind based on deadline proximity
            if task.deadline:
                time_until_deadline = task.deadline - now
                reminder_threshold = timedelta(minutes=reminder.interval_minutes)
                
                # Check if we're within the reminder window
                if timedelta(0) <= time_until_deadline <= reminder_threshold:
                    # Check if we haven't reminded recently (within last 30 minutes)
                    if not reminder.last_triggered or (now - reminder.last_triggered) >= timedelta(minutes=30):
                        should_remind = True
                        if reminder.interval_minutes == 15:
                            reminder_message = f"⏰ Task '{task.title}' deadline in 15 minutes!"
                        elif reminder.interval_minutes == 30:
                            reminder_message = f"⏰ Task '{task.title}' deadline in 30 minutes!"
                        elif reminder.interval_minutes == 60:
                            reminder_message = f"⏰ Task '{task.title}' deadline in 1 hour!"
                        elif reminder.interval_minutes == 180:
                            reminder_message = f"⏰ Task '{task.title}' deadline in 3 hours!"
        
        elif reminder.reminder_type == 'daily':
            # Check if it's time for daily reminder
            if reminder.custom_time:
                # Check if current time matches the reminder time (within 1 minute)
                reminder_hour = reminder.custom_time.hour
                reminder_minute = reminder.custom_time.minute
                
                if now.hour == reminder_hour and now.minute == reminder_minute:
                    # Check if we haven't reminded today
                    if not reminder.last_triggered or reminder.last_triggered.date() < now.date():
                        should_remind = True
                        reminder_message = f"📅 Daily reminder: '{task.title}'"
        
        elif reminder.reminder_type == 'custom':
            # Check if custom time has passed
            if reminder.custom_time and now >= reminder.custom_time:
                # Check if we haven't triggered this one-time reminder yet
                if not reminder.last_triggered:
                    should_remind = True
                    reminder_message = f"🔔 Reminder: '{task.title}'"
                    # Deactivate one-time custom reminders after triggering
                    reminder.is_active = False
        
        if should_remind:
            reminder.last_triggered = now
            due_reminders.append({
                'task_id': task.id,
                'task_title': task.title,
                'reminder_id': reminder.id,
                'reminder_type': reminder.reminder_type,
                'message': reminder_message,
                'priority': task.priority,
                'github_issue_url': task.github_issue_url
            })
    
    if due_reminders:
        db.session.commit()
    
    return jsonify(due_reminders)


# FCP Manager API endpoints
@app.route('/api/fcp/trigger', methods=['POST'])
def fcp_trigger_pipeline():
    """Trigger FCP pipeline"""
    import subprocess
    data = request.json
    
    service_name = data.get('service_name')
    mode = data.get('mode', '1')  # 1 = trigger, 2 = create
    
    if not service_name:
        return jsonify({'error': 'Service name is required'}), 400
    
    try:
        # Path to fcp_manager script
        script_path = '/Users/sreekanthchityala/nettools/internal-scripts/fcp/fcp_manager.sh'
        
        # For mode 1 (trigger), pass service name as argument
        if mode == '1':
            cmd = ['bash', script_path, service_name]
        else:
            # For mode 2 (create), we'll need interactive input
            return jsonify({'error': 'Create mode requires interactive terminal'}), 400
        
        # Execute the script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr if result.returncode != 0 else None
        })
    
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Script execution timed out'}), 408
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fcp/history')
def fcp_get_history():
    """Get FCP execution history"""
    try:
        history_file = os.path.expanduser('~/.fcp_manager_history')
        if not os.path.exists(history_file):
            return jsonify([])
        
        history = []
        with open(history_file, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 5:
                    history.append({
                        'service': parts[0],
                        'toolchain_guid': parts[1],
                        'toolchain_name': parts[2],
                        'trigger_id': parts[3],
                        'trigger_name': parts[4]
                    })
        
        return jsonify(history[:10])  # Return last 10
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fcp/dcs')
def fcp_get_dcs():
    """Get list of available DCs"""
    dcs = [
        {'id': 'syd05', 'name': 'Sydney 05', 'full': 'syd0501'},
        {'id': 'lon02', 'name': 'London 02', 'full': 'lon0201'},
        {'id': 'lon05', 'name': 'London 05', 'full': 'lon0501'},
        {'id': 'lon06', 'name': 'London 06', 'full': 'lon0601'},
        {'id': 'osa23', 'name': 'Osaka 23', 'full': 'osa2301'},
        {'id': 'syd04', 'name': 'Sydney 04', 'full': 'syd0401'}
    ]
    return jsonify(dcs)

# New FCP Wizard API Endpoints
@app.route('/fcp/wizard')
def fcp_wizard():
    """FCP Manager Wizard Page"""
    return render_template('fcp_wizard.html', active_page='fcp')

@app.route('/api/fcp/search-toolchains', methods=['POST'])
def fcp_search_toolchains():
    """Search for toolchains by service name"""
    try:
        data = request.get_json()
        service_name = data.get('service_name', '').strip()
        pipeline_type = data.get('pipeline_type')
        
        # Default to 'cd' if pipeline_type is not provided (for Create mode)
        if not pipeline_type:
            pipeline_type = 'cd'
        
        print(f"DEBUG: Searching for service: {service_name}, pipeline_type: {pipeline_type}")
        
        if not service_name:
            return jsonify({'success': False, 'error': 'Service name is required'})
        
        # Use IBM Cloud CLI to search for toolchains
        import subprocess
        import json as json_module
        
        # Determine the toolchain suffix based on pipeline type
        toolchain_suffix = '-ci' if pipeline_type == 'ci' else '-cd'
        
        # Get all toolchains and filter with jq (case-insensitive search)
        cmd = f'''ibmcloud dev toolchains --output json | jq -r --arg service "{service_name.lower()}" --arg suffix "{toolchain_suffix}" '
            .items[]
            | select(.name | ascii_downcase | contains($service))
            | select(.name | contains($suffix))
            | {{name, toolchain_guid}}
        ' | jq -s .'''
        
        print(f"DEBUG: Running command: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        print(f"DEBUG: Command return code: {result.returncode}")
        print(f"DEBUG: Command stdout: {result.stdout[:500] if result.stdout else 'empty'}")
        print(f"DEBUG: Command stderr: {result.stderr[:200] if result.stderr else 'empty'}")
        
        if result.returncode != 0:
            return jsonify({'success': False, 'error': f'Command failed: {result.stderr}'})
        
        if not result.stdout.strip() or result.stdout.strip() == '[]':
            # Try to get all toolchains to help debug
            debug_cmd = f'''ibmcloud dev toolchains --output json | jq -r '.items[] | select(.name | contains("{toolchain_suffix}")) | .name' | head -10'''
            debug_result = subprocess.run(debug_cmd, shell=True, capture_output=True, text=True, timeout=30)
            available_examples = debug_result.stdout.strip().split('\n')[:5] if debug_result.stdout else []
            
            error_msg = f'No {pipeline_type.upper()} toolchains found for "{service_name}".'
            if available_examples:
                error_msg += f' Available {pipeline_type.upper()} toolchains include: {", ".join(available_examples)}'
            
            return jsonify({'success': False, 'error': error_msg})
        
        # Parse JSON output
        toolchains = json_module.loads(result.stdout)
        
        print(f"DEBUG: Found {len(toolchains)} {pipeline_type.upper()} toolchains: {toolchains}")
        
        if not toolchains:
            return jsonify({'success': False, 'error': f'No {pipeline_type.upper()} toolchains found for "{service_name}"'})
        
        return jsonify({'success': True, 'toolchains': toolchains})
        
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception in search: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/fcp/get-triggers', methods=['POST'])
def fcp_get_triggers():
    """Get triggers for a toolchain"""
    try:
        data = request.get_json()
        toolchain_guid = data.get('toolchain_guid')
        pipeline_type = data.get('pipeline_type', 'cd')  # Default to 'cd' for backward compatibility
        
        print(f"DEBUG: Getting {pipeline_type.upper()} triggers for toolchain: {toolchain_guid}")
        
        if not toolchain_guid:
            return jsonify({'success': False, 'error': 'Toolchain GUID is required'})
        
        # Get IAM token
        iam_token = get_iam_token()
        if not iam_token:
            return jsonify({'success': False, 'error': 'Failed to get IAM token'})
        
        # Get pipeline ID
        pipeline_id = get_pipeline_id(toolchain_guid, iam_token)
        if not pipeline_id:
            return jsonify({'success': False, 'error': 'Failed to get pipeline ID'})
        
        print(f"DEBUG: Pipeline ID: {pipeline_id}")
        
        # Get triggers via API
        url = f"https://api.us-south.devops.cloud.ibm.com/pipeline/v2/tekton_pipelines/{pipeline_id}/triggers"
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"DEBUG: API error: {response.status_code} - {response.text}")
            return jsonify({'success': False, 'error': f'API error: {response.status_code}'})
        
        # Extract triggers based on pipeline type
        triggers_data = response.json()
        triggers = []
        
        for trigger in triggers_data.get('triggers', []):
            trigger_type = trigger.get('type', '')
            
            # Filter based on pipeline type
            if pipeline_type == 'cd':
                # CD pipelines: manual triggers
                if trigger_type == 'manual':
                    triggers.append({
                        'id': trigger.get('id'),
                        'name': trigger.get('name'),
                        'type': trigger_type,
                        'enabled': trigger.get('enabled', True)
                    })
            elif pipeline_type == 'ci':
                # CI pipelines: git, scm, github, gitlab triggers
                if trigger_type in ['git', 'scm', 'github', 'gitlab', 'generic']:
                    triggers.append({
                        'id': trigger.get('id'),
                        'name': trigger.get('name'),
                        'type': trigger_type,
                        'enabled': trigger.get('enabled', True)
                    })
        
        print(f"DEBUG: Found {len(triggers)} {pipeline_type.upper()} triggers")
        
        return jsonify({'success': True, 'triggers': triggers})
        
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/fcp/get-trigger-properties', methods=['POST'])
def fcp_get_trigger_properties():
    """Get trigger properties for editing"""
    try:
        data = request.get_json()
        toolchain_guid = data.get('toolchain_guid')
        trigger_id = data.get('trigger_id')
        
        print(f"DEBUG: Getting properties for trigger: {trigger_id}")
        
        if not toolchain_guid or not trigger_id:
            return jsonify({'success': False, 'error': 'Toolchain GUID and Trigger ID are required'})
        
        # Get IAM token
        iam_token = get_iam_token()
        if not iam_token:
            return jsonify({'success': False, 'error': 'Failed to get IAM token'})
        
        # Get pipeline ID
        pipeline_id = get_pipeline_id(toolchain_guid, iam_token)
        if not pipeline_id:
            return jsonify({'success': False, 'error': 'Failed to get pipeline ID'})
        
        # Get trigger details via API
        url = f"https://api.us-south.devops.cloud.ibm.com/pipeline/v2/tekton_pipelines/{pipeline_id}/triggers/{trigger_id}"
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"DEBUG: API error: {response.status_code} - {response.text}")
            return jsonify({'success': False, 'error': f'API error: {response.status_code}'})
        
        trigger_data = response.json()
        properties = trigger_data.get('properties', [])
        
        # Also fetch pipeline's global/default properties
        pipeline_url = f"https://api.us-south.devops.cloud.ibm.com/pipeline/v2/tekton_pipelines/{pipeline_id}"
        pipeline_response = requests.get(pipeline_url, headers=headers, timeout=30)
        
        global_properties = {}
        if pipeline_response.status_code == 200:
            pipeline_data = pipeline_response.json()
            for prop in pipeline_data.get('properties', []):
                global_properties[prop.get('name')] = prop.get('value', '')
            print(f"DEBUG: Found {len(global_properties)} global pipeline properties")
        
        # Format properties for frontend
        formatted_properties = []
        for prop in properties:
            formatted_properties.append({
                'name': prop.get('name'),
                'value': prop.get('value', ''),
                'type': prop.get('type', 'text'),
                'enum': prop.get('enum', []),
                'path': prop.get('path', '')
            })
        
        print(f"DEBUG: Found {len(formatted_properties)} trigger properties")
        
        return jsonify({
            'success': True,
            'properties': formatted_properties,
            'global_properties': global_properties,
            'trigger_name': trigger_data.get('name'),
            'pipeline_id': pipeline_id
        })
        
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/fcp/trigger-pipeline', methods=['POST'])
def fcp_trigger_pipeline_wizard():
    """Trigger a pipeline with optional property overrides"""
    try:
        data = request.get_json()
        toolchain_guid = data.get('toolchain_guid')
        trigger_id = data.get('trigger_id')
        property_overrides = data.get('properties', {})
        
        print(f"DEBUG: Triggering pipeline - trigger_id: {trigger_id}")
        print(f"DEBUG: Property overrides: {property_overrides}")
        
        if not toolchain_guid or not trigger_id:
            return jsonify({'success': False, 'error': 'Toolchain GUID and Trigger ID are required'})
        
        # Get IAM token
        iam_token = get_iam_token()
        if not iam_token:
            return jsonify({'success': False, 'error': 'Failed to get IAM token'})
        
        # Get pipeline ID
        pipeline_id = get_pipeline_id(toolchain_guid, iam_token)
        if not pipeline_id:
            return jsonify({'success': False, 'error': 'Failed to get pipeline ID'})
        
        # Get trigger details to get the trigger name
        trigger_url = f"https://api.us-south.devops.cloud.ibm.com/pipeline/v2/tekton_pipelines/{pipeline_id}/triggers/{trigger_id}"
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        }
        
        trigger_response = requests.get(trigger_url, headers=headers, timeout=30)
        if trigger_response.status_code != 200:
            return jsonify({'success': False, 'error': 'Failed to get trigger details'})
        
        trigger_data = trigger_response.json()
        trigger_name = trigger_data.get('name')
        
        print(f"DEBUG: Trigger name: {trigger_name}")
        
        # Trigger pipeline via API
        run_url = f"https://api.us-south.devops.cloud.ibm.com/pipeline/v2/tekton_pipelines/{pipeline_id}/pipeline_runs"
        
        # Build payload with trigger name
        payload = {
            'trigger': {
                'name': trigger_name
            }
        }
        
        # Add property overrides if any
        if property_overrides:
            payload['trigger']['properties'] = property_overrides
        
        print(f"DEBUG: Trigger payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(run_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code not in [200, 201]:
            print(f"DEBUG: API error: {response.status_code} - {response.text}")
            return jsonify({'success': False, 'error': f'API error: {response.status_code}', 'details': response.text})
        
        run_data = response.json()
        run_id = run_data.get('id')
        
        # Build pipeline run URL
        pipeline_url = f"https://cloud.ibm.com/devops/pipelines/tekton/{pipeline_id}/runs/{run_id}"
        
        print(f"DEBUG: Pipeline triggered successfully - run_id: {run_id}")
        
        return jsonify({
            'success': True,
            'run_id': run_id,
            'pipeline_id': pipeline_id,
            'url': pipeline_url,
            'message': 'Pipeline triggered successfully'
        })
        
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)})
@app.route('/api/fcp/pipeline-status', methods=['POST'])
def fcp_pipeline_status():
    """Get pipeline run status and logs"""
    try:
        data = request.get_json()
        pipeline_id = data.get('pipeline_id')
        run_id = data.get('run_id')
        
        if not pipeline_id or not run_id:
            return jsonify({'success': False, 'error': 'Pipeline ID and Run ID are required'})
        
        # Get IAM token
        iam_token = get_iam_token()
        if not iam_token:
            return jsonify({'success': False, 'error': 'Failed to get IAM token'})
        
        # Get pipeline run status
        url = f"https://api.us-south.devops.cloud.ibm.com/pipeline/v2/tekton_pipelines/{pipeline_id}/pipeline_runs/{run_id}"
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return jsonify({'success': False, 'error': f'API error: {response.status_code}'})
        
        run_data = response.json()
        
        print(f"DEBUG: Pipeline run data: {json.dumps(run_data, indent=2)[:500]}")
        
        # Extract status - handle both string and dict formats
        status_data = run_data.get('status', {})
        if isinstance(status_data, str):
            status = status_data
        elif isinstance(status_data, dict):
            status = status_data.get('state', 'unknown')
        else:
            status = 'unknown'
        
        # Extract task runs
        task_runs = []
        for task_run in run_data.get('task_runs', []):
            task_status = task_run.get('status', {})
            if isinstance(task_status, str):
                task_state = task_status
            elif isinstance(task_status, dict):
                task_state = task_status.get('state', 'unknown')
            else:
                task_state = 'unknown'
                
            task_info = {
                'name': task_run.get('task_name', 'Unknown'),
                'status': task_state,
                'start_time': task_run.get('status', {}).get('start_time') if isinstance(task_run.get('status'), dict) else None,
                'completion_time': task_run.get('status', {}).get('completion_time') if isinstance(task_run.get('status'), dict) else None
            }
            task_runs.append(task_info)
        
        return jsonify({
            'success': True,
            'status': status,
            'task_runs': task_runs,
            'start_time': run_data.get('created_at'),
            'updated_at': run_data.get('updated_at')
        })
        
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)})



# ============================================================================
# FCP Manager Helper Functions (Python implementation)
# ============================================================================

def get_iam_token():
    """Get IBM Cloud IAM token"""
    try:
        result = subprocess.run(
            ['ibmcloud', 'iam', 'oauth-tokens', '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            tokens = json.loads(result.stdout)
            return tokens.get('iam_token', '').replace('Bearer ', '')
        return None
    except Exception as e:
        print(f"Error getting IAM token: {e}")
        return None

def get_pipeline_id(toolchain_guid, iam_token):
    """Get pipeline ID from toolchain"""
    try:
        result = subprocess.run(
            ['ibmcloud', 'dev', 'toolchain-get', toolchain_guid, '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            toolchain_data = json.loads(result.stdout)
            services = toolchain_data.get('items', [{}])[0].get('services', [])
            for service in services:
                if service.get('service_id') == 'pipeline':
                    return service.get('instance_id')
        return None
    except Exception as e:
        print(f"Error getting pipeline ID: {e}")
        return None

def fetch_template_trigger(iam_token, dc):
    """Fetch template trigger from log-alerts"""
    try:
        log_alerts_pipeline_id = "a00fb3e6-c0ca-4e93-ba45-8f32c395790b"
        template_dc = "syd05"
        
        url = f"https://api.us-south.devops.cloud.ibm.com/pipeline/v2/tekton_pipelines/{log_alerts_pipeline_id}/triggers"
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"DEBUG: Fetching template from {url}")
        response = requests.get(url, headers=headers, timeout=30)
        print(f"DEBUG: Response status: {response.status_code}")
        
        if response.status_code == 200:
            triggers = response.json().get('triggers', [])
            print(f"DEBUG: Found {len(triggers)} triggers")
            # Pattern is "FCP-prod syd05" not "FCP-prod (syd05)"
            pattern = f"FCP-prod {template_dc}"
            print(f"DEBUG: Looking for pattern: {pattern}")
            for trigger in triggers:
                trigger_name = trigger.get('name', '')
                if pattern in trigger_name:
                    print(f"DEBUG: Found matching template trigger: {trigger_name}")
                    return trigger
            print(f"DEBUG: No matching trigger found for pattern '{pattern}'")
        else:
            print(f"DEBUG: API error: {response.text}")
        return None
    except Exception as e:
        print(f"Error fetching template trigger: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_worker_config(toolchain_guid, iam_token, dc=None):
    """Get worker configuration from toolchain for specific DC"""
    try:
        result = subprocess.run(
            ['ibmcloud', 'dev', 'toolchain-get', toolchain_guid, '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            toolchain_data = json.loads(result.stdout)
            services = toolchain_data.get('items', [{}])[0].get('services', [])
            
            # If DC is specified, look for DC-specific worker first
            if dc:
                expected_worker_name = f'fcp-{dc}-nettools-cd-worker'
                print(f"DEBUG: Looking for worker: {expected_worker_name}")
                
                for service in services:
                    if service.get('service_id') == 'private_worker':
                        worker_name = service.get('parameters', {}).get('name', '')
                        print(f"DEBUG: Found worker: {worker_name}")
                        if worker_name == expected_worker_name:
                            print(f"DEBUG: Matched DC-specific worker: {worker_name}")
                            return {
                                'id': service.get('instance_id'),
                                'name': worker_name
                            }
                
                # If DC-specific worker not found, return error
                print(f"DEBUG: DC-specific worker '{expected_worker_name}' not found")
                return None
            
            # If no DC specified, return first worker found
            for service in services:
                if service.get('service_id') == 'private_worker':
                    return {
                        'id': service.get('instance_id'),
                        'name': service.get('parameters', {}).get('name', 'worker')
                    }
        return None
    except Exception as e:
        print(f"Error getting worker config: {e}")
        return None

def create_worker_integration(toolchain_guid, iam_token, dc, service_name):
    """Create a new private worker integration in the toolchain"""
    try:
        worker_name = f"FCP-{dc.upper()}-{service_name.upper()}-TEKTON-CDWORKER"
        print(f"DEBUG: Creating worker: {worker_name}")
        
        # Create worker using IBM Cloud CLI
        result = subprocess.run(
            [
                'ibmcloud', 'dev', 'toolchain-service-create',
                toolchain_guid,
                '--service-id', 'private_worker',
                '--parameters', json.dumps({
                    'name': worker_name,
                    'worker_queue_identifier': worker_name.lower(),
                    'worker_queue_credentials': ''
                }),
                '--output', 'json'
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            worker_data = json.loads(result.stdout)
            print(f"DEBUG: Worker created successfully: {worker_data}")
            return {
                'id': worker_data.get('instance_id'),
                'name': worker_name
            }
        else:
            print(f"ERROR: Failed to create worker: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"Error creating worker integration: {e}")
        return None

def get_secrets_manager_integration(toolchain_guid, iam_token):
    """Get Secrets Manager integration ID from toolchain"""
    try:
        result = subprocess.run(
            ['ibmcloud', 'dev', 'toolchain-get', toolchain_guid, '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            toolchain_data = json.loads(result.stdout)
            services = toolchain_data.get('items', [{}])[0].get('services', [])
            for service in services:
                # Look for Secrets Manager integration (prod-sm)
                if service.get('service_id') == 'secretsmanager':
                    service_name = service.get('parameters', {}).get('name', '')
                    if 'prod-sm' in service_name.lower():
                        return service.get('instance_id')
        return None
    except Exception as e:
        print(f"Error getting Secrets Manager integration: {e}")
        return None

def detect_pipeline_config_branch(pipeline_id, iam_token):
    """Detect pipeline-config-branch from existing triggers"""
    try:
        url = f"https://api.us-south.devops.cloud.ibm.com/pipeline/v2/tekton_pipelines/{pipeline_id}/triggers"
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            triggers = response.json().get('triggers', [])
            for trigger in triggers:
                if 'FCP' in trigger.get('name', ''):
                    properties = trigger.get('properties', [])
                    for prop in properties:
                        if prop.get('name') == 'pipeline-config-branch':
                            return prop.get('value', 'master')
            return 'master'  # Default
        return 'master'
    except Exception as e:
        print(f"Error detecting pipeline-config-branch: {e}")
        return 'master'

def create_trigger_payload(trigger_name, template_trigger, worker_config, dc, pipeline_config_branch, sm_integration_id=None):
    """Create trigger payload with hardcoded defaults"""
    
    # DC mapping for cluster names
    dc_cluster_map = {
        'syd05': 'rkeranchersyd0501.softlayer.local',
        'syd04': 'rkeranchersyd0401.softlayer.local',
        'lon02': 'rkerancherlon0201.softlayer.local',
        'lon05': 'rkerancherlon0501.softlayer.local',
        'lon06': 'rkerancherlon0601.softlayer.local',
        'osa23': 'rkerancherosa2301.softlayer.local'
    }
    
    dc_downstream_map = {
        'syd05': 'rkecontrolsyd0501',
        'syd04': 'rkecontrolsyd0401',
        'lon02': 'rkecontrollon0201',
        'lon05': 'rkecontrollon0501',
        'lon06': 'rkecontrollon0601',
        'osa23': 'rkecontrolosa2301'
    }
    
    # Build properties list
    properties = [
        {'name': 'classic-user-creds', 'value': 'oculus-classic-production-fid', 'type': 'secure'},
        {'name': 'fcp_cluster', 'value': dc_cluster_map.get(dc, 'rkeranchersyd0501.softlayer.local'), 'type': 'text'},
        {'name': 'fcp_downstream_cluster', 'value': dc_downstream_map.get(dc, 'rkecontrolsyd0501'), 'type': 'text'},
        {'name': 'k8_replacement_list', 'value': f'auth/k8s-cluster-dc::>auth/k8s-cluster-{dc}01', 'type': 'text'},
        {'name': 'namespace', 'value': 'network-monitoring', 'type': 'text'},
        {'name': 'pipeline-config-branch', 'value': 'fcp-classic-pipeline', 'type': 'text'},
        {'name': 'repo-branch', 'value': 'fcp-dev', 'type': 'text'},
        {'name': 'sm-secret-grp', 'value': 'classic', 'type': 'text'},
        {'name': 'target-environment', 'value': 'fcp-dev', 'type': 'text'},
        {'name': 'vault-token', 'value': 'fcp-dal14-vault-token', 'type': 'secure'},
        {'name': 'vault_addr_url', 'value': 'http://172.27.21.98:8200', 'type': 'text'}
    ]
    
    # Add Secrets Manager integration if available
    if sm_integration_id:
        properties.append({
            'name': 'nettools-sm',
            'value': sm_integration_id,
            'type': 'integration'
        })
    
    # Create trigger with hardcoded defaults
    new_trigger = {
        'name': trigger_name,
        'type': 'manual',
        'event_listener': 'dev-mode-cd-listener',
        'worker': {
            'id': worker_config['id']
        },
        'properties': properties,
        'enabled': True
    }
    
    return new_trigger

def post_trigger(pipeline_id, trigger_payload, iam_token):
    """Post new trigger to pipeline"""
    try:
        url = f"https://api.us-south.devops.cloud.ibm.com/pipeline/v2/tekton_pipelines/{pipeline_id}/triggers"
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, json=trigger_payload, timeout=30)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"Error posting trigger: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error posting trigger: {e}")
        return None

@app.route('/api/fcp/create-trigger', methods=['POST'])
def fcp_create_trigger_wizard():
    """Create a new trigger using Python/IBM Cloud API"""
    try:
        data = request.get_json()
        print(f"DEBUG: Received data: {data}")  # Debug log
        
        service_name = data.get('service_name')
        dc = data.get('dc')
        toolchain_guid = data.get('toolchain_guid')
        
        print(f"DEBUG: service_name={service_name}, dc={dc}, toolchain_guid={toolchain_guid}")  # Debug log
        
        if not service_name or not dc or not toolchain_guid:
            return jsonify({
                'success': False,
                'error': f'Missing required fields - service_name: {service_name}, dc: {dc}, toolchain_guid: {toolchain_guid}'
            })
        
        # Get IAM token
        iam_token = get_iam_token()
        if not iam_token:
            return jsonify({'success': False, 'error': 'Failed to get IAM token'})
        
        # Get pipeline ID
        pipeline_id = get_pipeline_id(toolchain_guid, iam_token)
        if not pipeline_id:
            return jsonify({'success': False, 'error': 'Failed to get pipeline ID'})
        
        # Get worker configuration for specific DC
        worker_config = get_worker_config(toolchain_guid, iam_token, dc)
        if not worker_config:
            # Worker not found, return error to show modal
            print(f"DEBUG: Worker fcp-{dc}-nettools-cd-worker not found")
            return jsonify({
                'success': False,
                'worker_not_found': True,
                'dc': dc,
                'expected_worker': f'fcp-{dc}-nettools-cd-worker',
                'message': f'Worker "fcp-{dc}-nettools-cd-worker" not found. Please create it manually using the modal.'
            })
        
        # Get Secrets Manager integration
        sm_integration_id = get_secrets_manager_integration(toolchain_guid, iam_token)
        if not sm_integration_id:
            print("Warning: Secrets Manager integration not found, trigger may fail")
        
        # Create the trigger with hardcoded defaults
        trigger_name = f"Manual CD Trigger - {service_name} - FCP-prod {dc}"
        new_trigger = create_trigger_payload(
            trigger_name,
            None,  # No template needed
            worker_config,
            dc,
            None,  # No pipeline_config_branch needed
            sm_integration_id  # Pass SM integration ID
        )
        
        # Debug: Print the trigger payload
        print(f"DEBUG: Trigger payload: {json.dumps(new_trigger, indent=2)}")
        
        # Post the trigger
        result = post_trigger(pipeline_id, new_trigger, iam_token)
        
        if result:
            return jsonify({
                'success': True,
                'trigger_id': result.get('id'),
                'trigger_name': result.get('name'),
                'message': f'Trigger created successfully for {dc}'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create trigger'})
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})

@app.route('/api/fcp/open-terminal', methods=['POST'])
def fcp_open_terminal():
    """Open terminal with FCP Manager script"""
    try:
        data = request.get_json()
        script_path = data.get('script_path', '/Users/sreekanthchityala/nettools/internal-scripts/fcp/fcp_manager.sh')
        
        # Open Terminal.app on macOS
        import subprocess
        cmd = f"osascript -e 'tell application \"Terminal\" to do script \"cd ~ && bash {script_path}\"'"
        subprocess.Popen(cmd, shell=True)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

        
        if 'created' in result.stdout.lower() or 'success' in result.stdout.lower():
            return jsonify({
                'success': True,
                'output': result.stdout,
                'dc': dc
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create trigger',
                'output': result.stdout + result.stderr
            })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/fcp/check-auth', methods=['GET'])
def fcp_check_auth():
    """Check if user is authenticated with IBM Cloud"""
    try:
        import subprocess
        
        # Check IBM Cloud login status
        result = subprocess.run(['ibmcloud', 'target'], capture_output=True, text=True)
        
        if result.returncode == 0 and 'logged in' in result.stdout.lower():
            return jsonify({'success': True, 'authenticated': True})
        else:
            return jsonify({'success': True, 'authenticated': False})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Get host and port from environment or use defaults
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    app.run(host=host, port=port, debug=debug)

# Made with Bob

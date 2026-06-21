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

class Datacenter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # e.g., che01, dal09, syd05
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    return redirect(url_for('github_page'))

@app.route('/github')
def github_page():
    return render_template('github.html', active_page='github')


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
@app.route('/api/datacenters', methods=['GET', 'POST'])
def datacenters():
    """Get all datacenters or create a new one"""
    if request.method == 'POST':
        data = request.json
        dc_name = data['name'].lower().strip()
        
        # Check if DC already exists
        existing_dc = Datacenter.query.filter_by(name=dc_name).first()
        if existing_dc:
            return jsonify({'error': 'Datacenter already exists', 'id': existing_dc.id}), 409
        
        dc = Datacenter(
            name=dc_name,
            description=data.get('description', '')
        )
        db.session.add(dc)
        db.session.commit()
        print(f"DEBUG: Created new datacenter: {dc_name}")
        return jsonify({'id': dc.id, 'name': dc.name, 'message': 'Datacenter created successfully'})
    
    # GET request - return all datacenters
    datacenters = Datacenter.query.order_by(Datacenter.name).all()
    return jsonify([{
        'id': dc.id,
        'name': dc.name,
        'description': dc.description,
        'created_at': dc.created_at.isoformat()
    } for dc in datacenters])

@app.route('/api/datacenters/<int:dc_id>', methods=['DELETE'])
def datacenter_detail(dc_id):
    """Delete a datacenter"""
    dc = Datacenter.query.get_or_404(dc_id)
    db.session.delete(dc)
    db.session.commit()
    return jsonify({'message': 'Datacenter deleted successfully'})


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
    return jsonify({
        'github_username': '',
        'has_token': False
    })

@app.route('/api/fcp/create-inventory-branch', methods=['POST'])
def create_inventory_branch():
    """
    Create inventory branch for services that require it
    
    Request body:
    {
        "service_name": "ngdc-tsdb-cluster",
        "dc": "dal12",
        "base_branch": "fcp-dev"
    }
    
    Response:
    {
        "success": true,
        "branch_name": "fcp-dal1201",
        "repository": "ngdc-tsdb-cluster-inventory",
        "url": "https://github.ibm.com/nettools/ngdc-tsdb-cluster-inventory/tree/fcp-dal1201",
        "message": "Branch created successfully"
    }
    """
    data = request.json
    service_name = data.get('service_name')
    dc = data.get('dc')
    base_branch = data.get('base_branch', 'fcp-dev')
    
    # Service to repository mapping
    INVENTORY_REPOS = {
        'ngdc-tsdb-cluster': 'ngdc-tsdb-cluster-inventory',
        # Add more services here as needed
    }
    
    if service_name not in INVENTORY_REPOS:
        return jsonify({
            'success': False,
            'error': f'No inventory repository configured for {service_name}'
        }), 400
    
    repo_name = INVENTORY_REPOS[service_name]
    # Normalize DC name (e.g., dal12 -> dal1201)
    dc_full = f"{dc}01" if len(dc) == 5 else dc
    branch_name = f"fcp-{dc_full}"
    
    try:
        # Use /tmp for temporary git operations
        repo_path = f"/tmp/{repo_name}"
        repo_url = f"git@github.ibm.com:nettools/{repo_name}.git"
        
        app.logger.info(f"Creating inventory branch {branch_name} for {service_name} in {repo_name}")
        
        # Clone or update repository
        if not os.path.exists(repo_path):
            app.logger.info(f"Cloning repository {repo_name}...")
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', '--single-branch', '--branch', base_branch, repo_url, repo_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                app.logger.error(f"Failed to clone: {result.stderr}")
                return jsonify({
                    'success': False,
                    'error': f'Failed to clone repository: {result.stderr}'
                }), 500
        
        # Save current directory
        original_dir = os.getcwd()
        
        try:
            # Change to repo directory
            os.chdir(repo_path)
            
            # Fetch latest changes for the specific branch
            app.logger.info(f"Fetching branch {branch_name}...")
            subprocess.run(['git', 'fetch', 'origin', f'{branch_name}:{branch_name}'],
                          capture_output=True, timeout=30)
            
            # Check if branch exists locally
            branch_check = subprocess.run(
                ['git', 'rev-parse', '--verify', branch_name],
                capture_output=True,
                timeout=5
            )
            
            if branch_check.returncode == 0:
                app.logger.info(f"Branch {branch_name} already exists")
                return jsonify({
                    'success': True,
                    'branch_name': branch_name,
                    'repository': repo_name,
                    'url': f'https://github.ibm.com/nettools/{repo_name}/tree/{branch_name}',
                    'message': 'Branch already exists',
                    'already_exists': True
                })
            
            # Ensure we're on base branch
            app.logger.info(f"Checking out {base_branch}...")
            subprocess.run(['git', 'checkout', base_branch], check=True, timeout=10, capture_output=True)
            subprocess.run(['git', 'pull', 'origin', base_branch], check=True, timeout=30, capture_output=True)
            
            # Create new branch
            app.logger.info(f"Creating branch {branch_name}...")
            subprocess.run(['git', 'checkout', '-b', branch_name], check=True, timeout=10, capture_output=True)
            
            # Push to remote
            app.logger.info(f"Pushing branch {branch_name} to remote...")
            subprocess.run(['git', 'push', 'origin', branch_name], check=True, timeout=30, capture_output=True)
            
            app.logger.info(f"Successfully created branch {branch_name}")
            return jsonify({
                'success': True,
                'branch_name': branch_name,
                'repository': repo_name,
                'url': f'https://github.ibm.com/nettools/{repo_name}/tree/{branch_name}',
                'message': 'Branch created successfully'
            })
            
        finally:
            # Always return to original directory
            os.chdir(original_dir)
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Git operation timed out. Please try again or create the branch manually.'
        }), 500
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8') if hasattr(e, 'stderr') and e.stderr else str(e)
        return jsonify({
            'success': False,
            'error': f'Git command failed: {error_msg}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500



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
        {'id': 'che01', 'name': 'Chennai 01', 'full': 'che0101'},
        {'id': 'dal09', 'name': 'Dallas 09', 'full': 'dal0901'},
        {'id': 'dal14', 'name': 'Dallas 14', 'full': 'dal1401'},
        {'id': 'fra05', 'name': 'Frankfurt 05', 'full': 'fra0501'},
        {'id': 'lon02', 'name': 'London 02', 'full': 'lon0201'},
        {'id': 'lon04', 'name': 'London 04', 'full': 'lon0401'},
        {'id': 'lon05', 'name': 'London 05', 'full': 'lon0501'},
        {'id': 'lon06', 'name': 'London 06', 'full': 'lon0601'},
        {'id': 'mad02', 'name': 'Madrid 02', 'full': 'mad0201'},
        {'id': 'mad04', 'name': 'Madrid 04', 'full': 'mad0401'},
        {'id': 'osa21', 'name': 'Osaka 21', 'full': 'osa2101'},
        {'id': 'osa22', 'name': 'Osaka 22', 'full': 'osa2201'},
        {'id': 'osa23', 'name': 'Osaka 23', 'full': 'osa2301'},
        {'id': 'sao01', 'name': 'Sao Paulo 01', 'full': 'sao0101'},
        {'id': 'sao04', 'name': 'Sao Paulo 04', 'full': 'sao0401'},
        {'id': 'sao05', 'name': 'Sao Paulo 05', 'full': 'sao0501'},
        {'id': 'sjc04', 'name': 'San Jose 04', 'full': 'sjc0401'},
        {'id': 'sng01', 'name': 'Singapore 01', 'full': 'sng0101'},
        {'id': 'syd04', 'name': 'Sydney 04', 'full': 'syd0401'},
        {'id': 'syd05', 'name': 'Sydney 05', 'full': 'syd0501'},
        {'id': 'tok02', 'name': 'Tokyo 02', 'full': 'tok0201'},
        {'id': 'tok04', 'name': 'Tokyo 04', 'full': 'tok0401'},
        {'id': 'tor01', 'name': 'Toronto 01', 'full': 'tor0101'},
        {'id': 'tor04', 'name': 'Toronto 04', 'full': 'tor0401'},
        {'id': 'tor05', 'name': 'Toronto 05', 'full': 'tor0501'},
        {'id': 'wdc04', 'name': 'Washington DC 04', 'full': 'wdc0401'}
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
        
        print(f"DEBUG: Searching for service: {service_name}")
        
        if not service_name:
            return jsonify({'success': False, 'error': 'Service name is required'})
        
        # Use IBM Cloud CLI to search for toolchains (same as bash script)
        import subprocess
        import json as json_module
        
        # Get all toolchains and filter with jq (same as bash script)
        cmd = f'''ibmcloud dev toolchains --output json | jq -r --arg service "{service_name}" '
            .items[]
            | select(.name | contains($service))
            | select(.name | contains("-cd"))
            | {{name, toolchain_guid}}
        ' | jq -s .'''
        
        print(f"DEBUG: Running command: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        print(f"DEBUG: Command return code: {result.returncode}")
        print(f"DEBUG: Command stdout: {result.stdout[:200] if result.stdout else 'empty'}")
        print(f"DEBUG: Command stderr: {result.stderr[:200] if result.stderr else 'empty'}")
        
        if result.returncode != 0:
            return jsonify({'success': False, 'error': f'Command failed: {result.stderr}'})
        
        if not result.stdout.strip():
            return jsonify({'success': False, 'error': 'No toolchains found'})
        
        # Parse JSON output
        toolchains = json_module.loads(result.stdout)
        
        print(f"DEBUG: Found {len(toolchains)} toolchains: {toolchains}")
        
        if not toolchains:
            return jsonify({'success': False, 'error': 'No toolchains found'})
        
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
        
        print(f"DEBUG: Getting triggers for toolchain: {toolchain_guid}")
        
        if not toolchain_guid:
            return jsonify({'success': False, 'error': 'Toolchain GUID is required'})
        
        # Get IAM token
        iam_token = get_iam_token()
        if not iam_token:
            return jsonify({
                'success': False,
                'error': 'IBM Cloud authentication required. A terminal window has been opened with login commands. Please complete the login and try again.',
                'needs_login': True
            })
        
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
        
        # Extract manual triggers
        triggers_data = response.json()
        triggers = []
        
        for trigger in triggers_data.get('triggers', []):
            if trigger.get('type') == 'manual':
                triggers.append({
                    'id': trigger.get('id'),
                    'name': trigger.get('name'),
                    'type': trigger.get('type'),
                    'enabled': trigger.get('enabled', True)
                })
        
        print(f"DEBUG: Found {len(triggers)} manual triggers")
        
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
            'pipeline_id': pipeline_id
        })
    except Exception as e:
        print(f"DEBUG: Error getting trigger properties: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/fcp/get-multi-trigger-properties', methods=['POST'])
def fcp_get_multi_trigger_properties():
    """Get properties from multiple triggers and show differences"""
    try:
        data = request.get_json()
        toolchain_guid = data.get('toolchain_guid')
        trigger_ids = data.get('trigger_ids', [])  # Array of trigger IDs
        
        print(f"DEBUG: Getting properties for {len(trigger_ids)} triggers")
        
        if not toolchain_guid or not trigger_ids:
            return jsonify({'success': False, 'error': 'Toolchain GUID and Trigger IDs are required'})
        
        # Get IAM token
        iam_token = get_iam_token()
        if not iam_token:
            return jsonify({'success': False, 'error': 'Failed to get IAM token'})
        
        # Get pipeline ID
        pipeline_id = get_pipeline_id(toolchain_guid, iam_token)
        if not pipeline_id:
            return jsonify({'success': False, 'error': 'Failed to get pipeline ID'})
        
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        }
        
        # Fetch properties from all triggers
        all_trigger_properties = []
        trigger_names = []
        
        for trigger_id in trigger_ids:
            url = f"https://api.us-south.devops.cloud.ibm.com/pipeline/v2/tekton_pipelines/{pipeline_id}/triggers/{trigger_id}"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                trigger_data = response.json()
                trigger_names.append(trigger_data.get('name', 'Unknown'))
                
                # Convert properties to dict for easy comparison
                props_dict = {}
                for prop in trigger_data.get('properties', []):
                    props_dict[prop.get('name')] = {
                        'value': prop.get('value', ''),
                        'type': prop.get('type', 'text')
                    }
                all_trigger_properties.append(props_dict)
        
        # Get global pipeline properties
        pipeline_url = f"https://api.us-south.devops.cloud.ibm.com/pipeline/v2/tekton_pipelines/{pipeline_id}"
        pipeline_response = requests.get(pipeline_url, headers=headers, timeout=30)
        
        global_properties = {}
        if pipeline_response.status_code == 200:
            pipeline_data = pipeline_response.json()
            for prop in pipeline_data.get('properties', []):
                global_properties[prop.get('name')] = prop.get('value', '')
        
        # Find all unique parameter names
        all_param_names = set()
        for props in all_trigger_properties:
            all_param_names.update(props.keys())
        
        # Compare parameters across triggers
        parameter_comparison = []
        for param_name in sorted(all_param_names):
            values = []
            param_type = 'text'
            
            for i, props in enumerate(all_trigger_properties):
                if param_name in props:
                    values.append(props[param_name]['value'])
                    param_type = props[param_name]['type']
                else:
                    values.append('')
            
            # Check if all values are the same
            unique_values = set(values)
            is_different = len(unique_values) > 1
            
            parameter_comparison.append({
                'name': param_name,
                'values': values,
                'type': param_type,
                'is_different': is_different,
                'unique_values': list(unique_values)
            })
        
        print(f"DEBUG: Compared {len(parameter_comparison)} parameters across {len(trigger_ids)} triggers")
        
        return jsonify({
            'success': True,
            'trigger_names': trigger_names,
            'parameter_comparison': parameter_comparison,
            'global_properties': global_properties,
            'pipeline_id': pipeline_id
        })
    except Exception as e:
        print(f"DEBUG: Error getting multi-trigger properties: {str(e)}")
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
        
        iam_token = get_iam_token()
        if not iam_token:
            return jsonify({'success': False, 'error': 'Failed to get IAM token'})
        
        pipeline_id = get_pipeline_id(toolchain_guid, iam_token)
        if not pipeline_id:
            return jsonify({'success': False, 'error': 'Failed to get pipeline ID'})
        
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
        
        run_url = f"https://api.us-south.devops.cloud.ibm.com/pipeline/v2/tekton_pipelines/{pipeline_id}/pipeline_runs"
        
        payload = {
            'trigger': {
                'name': trigger_name
            }
        }
        
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

@app.route('/api/fcp/update-trigger-properties', methods=['POST'])
def fcp_update_trigger_properties():
    """Update an existing trigger's properties without executing it"""
    try:
        data = request.get_json()
        toolchain_guid = data.get('toolchain_guid')
        trigger_id = data.get('trigger_id')
        property_overrides = data.get('properties', {}) or {}

        print(f"DEBUG: Updating trigger properties - trigger_id: {trigger_id}")
        print(f"DEBUG: Property overrides: {property_overrides}")

        if not toolchain_guid or not trigger_id:
            return jsonify({'success': False, 'error': 'Toolchain GUID and Trigger ID are required'})

        iam_token = get_iam_token()
        if not iam_token:
            return jsonify({'success': False, 'error': 'Failed to get IAM token'})

        pipeline_id = get_pipeline_id(toolchain_guid, iam_token)
        if not pipeline_id:
            return jsonify({'success': False, 'error': 'Failed to get pipeline ID'})

        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        }

        trigger_url = f"https://api.us-south.devops.cloud.ibm.com/pipeline/v2/tekton_pipelines/{pipeline_id}/triggers/{trigger_id}"
        trigger_response = requests.get(trigger_url, headers=headers, timeout=30)
        if trigger_response.status_code != 200:
            return jsonify({'success': False, 'error': 'Failed to get trigger details', 'details': trigger_response.text})

        trigger_data = trigger_response.json()
        existing_properties = trigger_data.get('properties', []) or []
        update_results = []

        for prop_name, prop_value in property_overrides.items():
            matching_prop = next((prop for prop in existing_properties if prop.get('name') == prop_name), None)
            property_payload = {
                'name': prop_name,
                'type': (matching_prop or {}).get('type', 'text'),
                'value': prop_value
            }
            property_url = f"https://api.us-south.devops.cloud.ibm.com/pipeline/v2/tekton_pipelines/{pipeline_id}/triggers/{trigger_id}/properties/{prop_name}"
            print(f"DEBUG: Update trigger property payload for {prop_name}: {json.dumps(property_payload, indent=2)}")

            update_response = requests.put(property_url, headers=headers, json=property_payload, timeout=30)
            if update_response.status_code not in [200, 201]:
                print(f"DEBUG: Update trigger API error: {update_response.status_code} - {update_response.text}")
                return jsonify({
                    'success': False,
                    'error': f'API error: {update_response.status_code}',
                    'details': update_response.text
                })

            update_results.append(update_response.json())

        return jsonify({
            'success': True,
            'trigger_id': trigger_id,
            'trigger_name': trigger_data.get('name'),
            'updated_properties': property_overrides,
            'results': update_results
        })
    except Exception as e:
        print(f"DEBUG: Error updating trigger properties: {str(e)}")
        import traceback
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

def open_terminal_with_login_commands():
    """Open a new terminal and run IBM Cloud login commands"""
    try:
        # Create a script with the login commands
        login_script = """#!/bin/bash
echo "=========================================="
echo "IBM Cloud Authentication Required"
echo "=========================================="
echo ""
echo "Running IBM Cloud login commands..."
echo ""

# Run the login commands
ibmcloud login --sso
ibmcloud cr login
ibmcloud target -g Default

echo ""
echo "=========================================="
echo "Authentication complete!"
echo "Please return to the application and try again."
echo "=========================================="
echo ""
read -p "Press Enter to close this terminal..."
"""
        
        # Write script to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(login_script)
            script_path = f.name
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        # Open terminal based on OS
        if os.uname().sysname == 'Darwin':  # macOS
            # Use osascript to open Terminal.app
            subprocess.Popen([
                'osascript', '-e',
                f'tell application "Terminal" to do script "{script_path}"'
            ])
        elif os.uname().sysname == 'Linux':
            # Try common Linux terminals
            terminals = ['gnome-terminal', 'konsole', 'xterm']
            for term in terminals:
                try:
                    subprocess.Popen([term, '-e', f'bash {script_path}'])
                    break
                except FileNotFoundError:
                    continue
        
        print(f"Opened terminal with login script: {script_path}")
        return True
    except Exception as e:
        print(f"Error opening terminal: {e}")
        return False

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
        
        # If failed, check if it's an authentication issue
        if 'not logged in' in result.stderr.lower() or 'authentication' in result.stderr.lower():
            print("IBM Cloud authentication required - opening terminal for login")
            open_terminal_with_login_commands()
            return None
        
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

def fetch_template_trigger(iam_token, pipeline_id, template_dc='syd04'):
    """Fetch template trigger from the current pipeline using a reference DC"""
    try:
        url = f"https://api.us-south.devops.cloud.ibm.com/pipeline/v2/tekton_pipelines/{pipeline_id}/triggers"
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        }

        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"DEBUG: Failed to fetch triggers for template lookup: {response.status_code} {response.text[:500]}")
            return None

        triggers = response.json().get('triggers', [])
        patterns = [
            f"FCP-prod {template_dc}",
            f"FCP {template_dc}",
            template_dc
        ]

        for trigger in triggers:
            trigger_name = trigger.get('name', '')
            if any(pattern in trigger_name for pattern in patterns):
                print(f"DEBUG: Found template trigger for {template_dc}: {trigger_name}")
                return trigger

        print(f"DEBUG: No template trigger found for reference DC '{template_dc}'")
        return None
    except Exception as e:
        print(f"Error fetching template trigger: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_worker_config(toolchain_guid, iam_token, dc=None):
    """Get worker configuration from toolchain for specific DC
    Returns:
        - Single worker dict if exactly one match found
        - List of worker dicts if multiple matches found
        - None if no matches found
    """
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
            
            # If DC is specified, look for workers matching the DC pattern
            if dc:
                dc_prefix = f'fcp-{dc}'
                print(f"DEBUG: Looking for workers starting with: {dc_prefix}")
                
                matching_workers = []
                for service in services:
                    if service.get('service_id') == 'private_worker':
                        worker_name = service.get('parameters', {}).get('name', '')
                        print(f"DEBUG: Found worker: {worker_name}")
                        
                        # Check if worker name starts with the DC prefix
                        if worker_name.lower().startswith(dc_prefix.lower()):
                            print(f"DEBUG: Matched DC worker: {worker_name}")
                            matching_workers.append({
                                'id': service.get('instance_id'),
                                'name': worker_name
                            })
                
                if len(matching_workers) == 0:
                    print(f"DEBUG: No workers found matching pattern '{dc_prefix}*'")
                    return None
                elif len(matching_workers) == 1:
                    print(f"DEBUG: Found single matching worker: {matching_workers[0]['name']}")
                    return matching_workers[0]
                else:
                    print(f"DEBUG: Found {len(matching_workers)} matching workers")
                    return matching_workers  # Return list for caller to handle selection
            
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

def get_toolchain_services(toolchain_guid):
    """Get raw toolchain services from IBM Cloud CLI"""
    try:
        result = subprocess.run(
            ['ibmcloud', 'dev', 'toolchain-get', toolchain_guid, '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"ERROR: Failed to get toolchain services: {result.stderr}")
            return None

        toolchain_data = json.loads(result.stdout)
        return toolchain_data.get('items', [{}])[0].get('services', [])
    except Exception as e:
        print(f"Error getting toolchain services: {e}")
        return None


def parse_secrets_manager_crn(secret_crn):
    secret_parts = secret_crn.split(':')
    if len(secret_parts) < 10:
        return None

    return {
        'instance_id': secret_parts[7],
        'region': secret_parts[5],
        'secret_id': secret_parts[-1]
    }


def fetch_secret_payload_from_crn(secret_crn, iam_token):
    parsed = parse_secrets_manager_crn(secret_crn)
    if not parsed:
        return {
            'success': False,
            'error': 'Invalid Secrets Manager CRN format',
            'secret_crn': secret_crn
        }

    secret_url = f"https://{parsed['instance_id']}.{parsed['region']}.secrets-manager.appdomain.cloud/api/v2/secrets/{parsed['secret_id']}"
    response = requests.get(
        secret_url,
        headers={
            'Authorization': f'Bearer {iam_token}',
            'Accept': 'application/json'
        },
        timeout=30
    )

    if response.status_code != 200:
        return {
            'success': False,
            'error': f'Failed to fetch worker credentials from Secrets Manager ({response.status_code})',
            'details': response.text[:500]
        }

    secret_payload = response.json().get('payload')
    if not secret_payload:
        return {
            'success': False,
            'error': 'Worker credentials payload missing in Secrets Manager secret'
        }

    return {
        'success': True,
        'credentials': secret_payload
    }


def get_secrets_manager_providers(toolchain_guid):
    services = get_toolchain_services(toolchain_guid)
    if services is None:
        return []

    providers = []
    for service in services:
        if service.get('service_id') != 'secretsmanager':
            continue

        parameters = service.get('parameters', {}) or {}
        provider_name = parameters.get('name') or service.get('name') or 'Secrets Manager'
        instance_crn = parameters.get('instance_crn') or parameters.get('crn') or ''
        region = parameters.get('region') or 'us-south'
        instance_id = ''

        if instance_crn:
            crn_parts = instance_crn.split(':')
            if len(crn_parts) > 7:
                instance_id = crn_parts[7]
            if len(crn_parts) > 5 and crn_parts[5]:
                region = crn_parts[5]

        providers.append({
            'id': service.get('instance_id') or instance_id or provider_name,
            'instance_id': instance_id,
            'name': provider_name,
            'instance_crn': instance_crn,
            'region': region,
            'private_endpoint': parameters.get('private_endpoint') or '',
            'public_endpoint': parameters.get('public_endpoint') or '',
            'endpoint': parameters.get('endpoint') or '',
            'secrets': parameters.get('secrets', []) or []
        })

    return providers


def get_secret_groups_for_provider(provider, iam_token):
    region = provider.get('region') or 'us-south'
    instance_id = provider.get('instance_id') or ''

    if not instance_id:
        return {
            'success': False,
            'error': 'Secrets Manager instance ID not found for selected provider'
        }

    base_url = (
        provider.get('public_endpoint')
        or provider.get('endpoint')
        or provider.get('private_endpoint')
        or f'https://{instance_id}.{region}.secrets-manager.appdomain.cloud'
    ).rstrip('/')

    response = requests.get(
        f'{base_url}/api/v2/secret_groups',
        headers={
            'Authorization': f'Bearer {iam_token}',
            'Accept': 'application/json'
        },
        timeout=30
    )

    if response.status_code != 200:
        return {
            'success': False,
            'error': f'Failed to fetch secret groups ({response.status_code})',
            'details': response.text[:500]
        }

    payload = response.json()
    resources = payload.get('secret_groups') or payload.get('resources') or []
    groups = [
        {
            'id': group.get('id') or group.get('name') or '',
            'name': group.get('name') or group.get('id') or 'Unnamed group'
        }
        for group in resources
        if group.get('id') or group.get('name')
    ]

    groups.sort(key=lambda item: item['name'].lower())
    return {
        'success': True,
        'groups': groups
    }


def find_secret_by_name(provider, group_id, secret_name, iam_token):
    region = provider.get('region') or 'us-south'
    instance_id = provider.get('instance_id') or ''

    if not instance_id:
        return {
            'success': False,
            'error': 'Secrets Manager instance ID not found for selected provider'
        }

    base_url = (
        provider.get('public_endpoint')
        or provider.get('endpoint')
        or provider.get('private_endpoint')
        or f'https://{instance_id}.{region}.secrets-manager.appdomain.cloud'
    ).rstrip('/')

    response = requests.get(
        f'{base_url}/api/v2/secrets',
        headers={
            'Authorization': f'Bearer {iam_token}',
            'Accept': 'application/json'
        },
        params={
            'groups': group_id,
            'search': secret_name
        },
        timeout=30
    )

    if response.status_code != 200:
        return {
            'success': False,
            'error': f'Failed to fetch secrets ({response.status_code})',
            'details': response.text[:500]
        }

    payload = response.json()
    resources = payload.get('resources') or payload.get('secrets') or []
    normalized_secret_name = secret_name.strip().lower()
    matched_secret = next(
        (
            secret for secret in resources
            if (secret.get('name') or '').strip().lower() == normalized_secret_name
        ),
        None
    )

    if not matched_secret:
        return {
            'success': False,
            'error': f'Secret "{secret_name}" not found in selected group'
        }

    return {
        'success': True,
        'secret': matched_secret
    }


def get_private_worker_credentials_from_toolchain(toolchain_guid, dc):
    """Resolve private worker queue credentials for a DC from toolchain integrations"""
    try:
        providers = get_secrets_manager_providers(toolchain_guid)
        if not providers:
            return {
                'success': False,
                'error': 'Secrets Manager integration not found in toolchain'
            }

        dc_secret_key = f'FCP-{dc}-SERVICEID-TEKTON-CDWORKER'.lower()
        matching_secret_ref = None

        for provider in providers:
            for secret_ref in provider.get('secrets', []):
                secret_name = (secret_ref.get('name') or '').lower()
                if secret_name == dc_secret_key:
                    matching_secret_ref = secret_ref
                    break
            if matching_secret_ref:
                break

        if not matching_secret_ref:
            return {
                'success': False,
                'error': f'Secret reference not found in toolchain for DC {dc}',
                'secret_name': f'FCP-{dc}-SERVICEID-TEKTON-CDWORKER',
                'needs_secret_selection': True,
                'providers': [
                    {
                        'id': provider['id'],
                        'name': provider['name']
                    }
                    for provider in providers
                ]
            }

        secret_crn = matching_secret_ref.get('crn')
        if not secret_crn:
            return {
                'success': False,
                'error': f'Secret CRN missing for DC {dc}',
                'secret_name': f'FCP-{dc}-SERVICEID-TEKTON-CDWORKER'
            }

        iam_token = get_iam_token()
        if not iam_token:
            return {
                'success': False,
                'error': 'Failed to get IAM token'
            }

        fetch_result = fetch_secret_payload_from_crn(secret_crn, iam_token)
        if not fetch_result.get('success'):
            return fetch_result

        return {
            'success': True,
            'credentials': fetch_result['credentials'],
            'secret_name': f'FCP-{dc}-SERVICEID-TEKTON-CDWORKER'
        }
    except Exception as e:
        print(f"Error resolving private worker credentials: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def create_worker_integration(toolchain_guid, iam_token, dc, service_name):
    """Create a new private worker integration in the toolchain using REST API"""
    try:
        worker_name = f"fcp-{dc}-nettools-cd-worker-{normalize_service_name(service_name)}"
        print(f"DEBUG: Creating worker via REST API: {worker_name}")

        existing_worker = get_worker_config(toolchain_guid, iam_token, dc)
        if isinstance(existing_worker, dict):
            return {
                'success': True,
                'worker': existing_worker,
                'created': False
            }
        if isinstance(existing_worker, list):
            return {
                'success': False,
                'multiple_workers': True,
                'workers': existing_worker,
                'error': f'Multiple workers already exist for {dc}'
            }

        credentials_result = get_private_worker_credentials_from_toolchain(toolchain_guid, dc)
        if not credentials_result.get('success'):
            return credentials_result

        payload = {
            'tool_type_id': 'private_worker',
            'name': worker_name,
            'parameters': {
                'name': worker_name,
                'worker_queue_credentials': credentials_result['credentials']
            }
        }

        response = requests.post(
            f'https://api.us-south.devops.cloud.ibm.com/toolchain/v2/toolchains/{toolchain_guid}/tools',
            headers={
                'Authorization': f'Bearer {iam_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            json=payload,
            timeout=60
        )

        if response.status_code not in (200, 201):
            return {
                'success': False,
                'error': f'Failed to create private worker ({response.status_code})',
                'details': response.text[:1000]
            }

        worker_data = response.json()
        worker = {
            'id': worker_data.get('id') or worker_data.get('tool_id') or worker_data.get('instance_id'),
            'name': worker_name
        }

        if not worker['id']:
            refreshed_worker = get_worker_config(toolchain_guid, iam_token, dc)
            if isinstance(refreshed_worker, dict):
                worker = refreshed_worker

        return {
            'success': True,
            'worker': worker,
            'created': True
        }
    except Exception as e:
        print(f"Error creating worker integration: {e}")
        return {
            'success': False,
            'error': str(e)
        }

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

def normalize_service_name(service_name):
    return service_name.rsplit('-cd', 1)[0].rsplit('-stage', 1)[0].rsplit('-prod', 1)[0]

def resolve_dc_files_repo_name(service_name):
    return normalize_service_name(service_name)

def resolve_inventory_repo_name(service_name):
    base_service = normalize_service_name(service_name)
    return f'{base_service}-inventory'

def build_dc_file_names(dc):
    return (
        f'fcp-{dc}01-deployment.yaml',
        f'fcp-{dc}01-values-enterprise.yaml'
    )

def build_dc_runtime_values(dc):
    return {
        'fcp_cluster': f'rkerancher{dc}01.softlayer.local',
        'fcp_downstream_cluster': f'rkecontrol{dc}01',
        'k8_replacement_list': f'auth/k8s-cluster-dc::>auth/k8s-cluster-{dc}01',
        'target-environment': f'fcp-{dc}01',
        'vault-token': 'fcp-dal14-vault-token'
    }

def rewrite_dc_value(value, source_dc, target_dc):
    if not isinstance(value, str) or not source_dc or not target_dc:
        return value

    source_dc = source_dc.lower().strip()
    target_dc = target_dc.lower().strip()

    replacements = [
        (f'rkerancher{source_dc}01.softlayer.local', f'rkerancher{target_dc}01.softlayer.local'),
        (f'rkecontrol{source_dc}01', f'rkecontrol{target_dc}01'),
        (f'auth/k8s-cluster-{source_dc}01', f'auth/k8s-cluster-{target_dc}01'),
        (f'fcp-{source_dc}01', f'fcp-{target_dc}01'),
        (f'-{source_dc}01', f'-{target_dc}01'),
        (source_dc, target_dc)
    ]

    rewritten = value
    for old, new in replacements:
        rewritten = rewritten.replace(old, new)

    return rewritten

def create_trigger_payload(trigger_name, template_trigger, worker_config, dc, pipeline_config_branch, sm_integration_id=None, property_overrides=None, source_dc=None):
    """Clone the reference trigger and only rewrite DC-specific values for the target DC."""
    runtime_values = build_dc_runtime_values(dc)
    source_dc = (source_dc or '').lower().strip()

    print(f"DEBUG: Rewriting trigger properties from reference DC '{source_dc}' to target DC '{dc}'")

    property_map = {}
    if template_trigger and template_trigger.get('properties'):
        for prop in template_trigger.get('properties', []):
            prop_name = prop.get('name')
            if not prop_name:
                continue

            property_map[prop_name] = {
                'name': prop_name,
                'value': rewrite_dc_value(prop.get('value'), source_dc, dc),
                'type': prop.get('type', 'text')
            }

    dc_specific_overrides = {
        'fcp_cluster': runtime_values['fcp_cluster'],
        'fcp_downstream_cluster': runtime_values['fcp_downstream_cluster'],
        'k8_replacement_list': runtime_values['k8_replacement_list'],
        'target-environment': runtime_values['target-environment'],
        'vault-token': runtime_values['vault-token']
    }

    for prop_name, prop_value in dc_specific_overrides.items():
        if prop_name in property_map:
            property_map[prop_name]['value'] = prop_value

    if sm_integration_id:
        if 'nettools-sm' in property_map:
            property_map['nettools-sm']['value'] = sm_integration_id
            property_map['nettools-sm']['type'] = property_map['nettools-sm'].get('type', 'integration') or 'integration'
        else:
            property_map['nettools-sm'] = {
                'name': 'nettools-sm',
                'value': sm_integration_id,
                'type': 'integration'
            }

    if property_overrides:
        for prop_name, prop_value in property_overrides.items():
            if prop_name in property_map:
                property_map[prop_name]['value'] = prop_value
            else:
                property_map[prop_name] = {
                    'name': prop_name,
                    'value': prop_value,
                    'type': 'text'
                }

    properties = list(property_map.values())

    payload = {
        'name': trigger_name,
        'type': template_trigger.get('type', 'manual') if template_trigger else 'manual',
        'event_listener': template_trigger.get('event_listener', 'dev-mode-cd-listener') if template_trigger else 'dev-mode-cd-listener',
        'worker': {
            'id': worker_config['id']
        },
        'properties': properties,
        'enabled': template_trigger.get('enabled', True) if template_trigger else True
    }

    return payload

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
            return {
                'success': True,
                'data': response.json()
            }

        error_text = response.text
        error_message = f'API error: {response.status_code}'
        trigger_exists = False

        try:
            error_json = response.json()
            errors = error_json.get('errors', [])
            if errors:
                trigger_exists = any(err.get('code') == 'non_unique_value' for err in errors)
                if trigger_exists:
                    error_message = 'Trigger already exists'
                else:
                    error_message = '; '.join(
                        err.get('message', 'Unknown API error')
                        for err in errors
                    )
            else:
                error_message = error_json.get('message', error_text)
        except Exception:
            error_message = error_text

        print(f"Error posting trigger: {response.status_code} - {response.text}")
        return {
            'success': False,
            'status_code': response.status_code,
            'error': error_message,
            'trigger_exists': trigger_exists,
            'details': error_text
        }
    except Exception as e:
        print(f"Error posting trigger: {e}")
        return {
            'success': False,
            'error': str(e),
            'trigger_exists': False
        }

@app.route('/api/fcp/create-trigger', methods=['POST'])
def fcp_create_trigger_wizard():
    """Create a new trigger using Python/IBM Cloud API"""
    try:
        data = request.get_json()
        print(f"DEBUG: Received data: {data}")  # Debug log
        
        service_name = data.get('service_name')
        dc = data.get('dc')
        toolchain_guid = data.get('toolchain_guid')
        file_action = data.get('file_action', 'skip')
        github_token = data.get('github_token')
        source_dc = data.get('source_dc')
        file_contents = data.get('file_contents') or {}
        property_overrides = data.get('property_overrides') or {}
        
        print(f"DEBUG: service_name={service_name}, dc={dc}, toolchain_guid={toolchain_guid}, file_action={file_action}")  # Debug log
        
        if not service_name or not dc or not toolchain_guid:
            return jsonify({
                'success': False,
                'error': f'Missing required fields - service_name: {service_name}, dc: {dc}, toolchain_guid: {toolchain_guid}'
            })
        
        base_service = normalize_service_name(service_name)
        files_repo = resolve_dc_files_repo_name(service_name)
        deployment_file, values_file = build_dc_file_names(dc)
        token = github_token or os.getenv('GITHUB_TOKEN')
        deployment_exists = False
        values_exists = False
        headers = None

        if not token:
            return jsonify({
                'success': False,
                'needs_token': True,
                'dc': dc,
                'service': base_service,
                'message': 'GitHub token required to verify or create DC files'
            })

        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        deployment_check_url = f'https://github.ibm.com/api/v3/repos/nettools/{files_repo}/contents/kubernetes/{deployment_file}?ref=fcp-develop'
        values_check_url = f'https://github.ibm.com/api/v3/repos/nettools/{files_repo}/contents/kubernetes/{values_file}?ref=fcp-develop'
        repo_tree_url = f'https://github.ibm.com/nettools/{files_repo}/tree/fcp-develop/kubernetes'

        def refresh_dc_file_status():
            deployment_response = requests.get(deployment_check_url, headers=headers, verify=True)
            values_response = requests.get(values_check_url, headers=headers, verify=True)
            print(f"DEBUG: Checking DC files for {dc} in repo {files_repo}")
            print(f"DEBUG: Deployment check URL: {deployment_check_url}")
            print(f"DEBUG: Deployment status: {deployment_response.status_code}")
            print(f"DEBUG: Values check URL: {values_check_url}")
            print(f"DEBUG: Values status: {values_response.status_code}")
            
            auth_failure_codes = {401, 403}
            if deployment_response.status_code in auth_failure_codes or values_response.status_code in auth_failure_codes:
                return None, None
            
            return deployment_response.status_code == 200, values_response.status_code == 200

        deployment_exists, values_exists = refresh_dc_file_status()

        if deployment_exists is None or values_exists is None:
            return jsonify({
                'success': False,
                'needs_token': True,
                'dc': dc,
                'service': files_repo,
                'message': 'GitHub authentication failed while verifying DC files. Please enter a valid token.'
            })

        skip_file_creation = file_action == 'skip-create-files'

        if not (deployment_exists and values_exists):
            if file_action == 'create':
                has_reviewed_file_contents = bool(file_contents.get('deployment_content')) and bool(file_contents.get('values_content'))

                if has_reviewed_file_contents:
                    save_payload = {
                        'dc': dc,
                        'service_name': service_name,
                        'deployment_content': file_contents['deployment_content'],
                        'values_content': file_contents['values_content'],
                        'github_token': token,
                        'target_branch': f'fcp-{dc}01',
                        'source_branch': 'fcp-dev'
                    }

                    with app.test_request_context(
                        '/api/fcp/save-dc-files',
                        method='POST',
                        json=save_payload
                    ):
                        save_response = save_dc_files()
                    save_payload_result = save_response.get_json()
                    if not save_payload_result.get('success'):
                        return jsonify(save_payload_result)

                    deployment_exists, values_exists = refresh_dc_file_status()
                    if not (deployment_exists and values_exists):
                        return jsonify({
                            'success': False,
                            'dc': dc,
                            'service': files_repo,
                            'message': f'DC files for {dc} were saved to fcp-develop but could not be verified on GitHub',
                            'repo_url': repo_tree_url,
                            'check_urls': {
                                'deployment': deployment_check_url,
                                'values': values_check_url
                            },
                            'files': {
                                'deployment': {
                                    'name': deployment_file,
                                    'exists': deployment_exists
                                },
                                'values': {
                                    'name': values_file,
                                    'exists': values_exists
                                }
                            }
                        })
                else:
                    generate_payload = {
                        'dc': dc,
                        'service_name': service_name,
                        'github_token': token,
                        'source_branch': 'fcp-dev',
                        'target_branch': f'fcp-{dc}01'
                    }
                    if source_dc:
                        generate_payload['source_dc'] = source_dc

                    with app.test_request_context(
                        '/api/fcp/generate-dc-files',
                        method='POST',
                        json=generate_payload
                    ):
                        generated_response = generate_dc_files()
                    generated_payload = generated_response.get_json()
                    if not generated_payload.get('success'):
                        return jsonify(generated_payload)

                    return jsonify({
                        'success': False,
                        'needs_file_creation': True,
                        'needs_file_review': True,
                        'dc': dc,
                        'service': files_repo,
                        'message': f'Review generated YAML files for {dc} before saving them to the repo',
                        'repo_url': repo_tree_url,
                        'check_urls': {
                            'deployment': deployment_check_url,
                            'values': values_check_url
                        },
                        'files': {
                            'deployment': {
                                'name': deployment_file,
                                'exists': deployment_exists
                            },
                            'values': {
                                'name': values_file,
                                'exists': values_exists
                            }
                        },
                        'generated_files': generated_payload.get('files', {})
                    })
            elif not skip_file_creation:
                return jsonify({
                    'success': False,
                    'missing_dc_files': True,
                    'dc': dc,
                    'service': files_repo,
                    'message': f'Missing DC files for {dc}',
                    'repo_url': repo_tree_url,
                    'check_urls': {
                        'deployment': deployment_check_url,
                        'values': values_check_url
                    },
                    'files': {
                        'deployment': {
                            'name': deployment_file,
                            'exists': deployment_exists
                        },
                        'values': {
                            'name': values_file,
                            'exists': values_exists
                        }
                    },
                    'needs_token': False
                })
        
        # Get IAM token
        iam_token = get_iam_token()
        if not iam_token:
            return jsonify({'success': False, 'error': 'Failed to get IAM token'})
        
        # Get pipeline ID
        pipeline_id = get_pipeline_id(toolchain_guid, iam_token)
        if not pipeline_id:
            return jsonify({'success': False, 'error': 'Failed to get pipeline ID'})
        
        reference_dc = (source_dc or 'syd04').strip().lower()
        print(f"DEBUG: Using reference DC '{reference_dc}' for service '{service_name}' in current pipeline")

        template_trigger = fetch_template_trigger(iam_token, pipeline_id, reference_dc)
        if not template_trigger:
            return jsonify({
                'success': False,
                'error': f"Reference trigger for {reference_dc} not found in current pipeline"
            })

        worker_config = get_worker_config(toolchain_guid, iam_token, dc)

        if isinstance(worker_config, list):
            return jsonify({
                'success': False,
                'multiple_workers': True,
                'dc': dc,
                'workers': [{'id': w['id'], 'name': w['name']} for w in worker_config],
                'message': f'Multiple workers found for {dc}. Please select one.'
            })

        if not worker_config or not worker_config.get('id'):
            return jsonify({
                'success': False,
                'worker_not_found': True,
                'dc': dc,
                'expected_worker': f'fcp-{dc}-nettools-cd-worker-{normalize_service_name(service_name)}',
                'message': f'DC-specific worker not found for {dc}. Create the worker first, then retry.'
            })

        sm_integration_id = get_secrets_manager_integration(toolchain_guid, iam_token)
        if not sm_integration_id:
            print("Warning: Secrets Manager integration not found, trigger may fail")

        dc_name = dc.lower().strip()
        existing_dc = Datacenter.query.filter_by(name=dc_name).first()
        if not existing_dc:
            new_dc = Datacenter(name=dc_name, description=f'Auto-created from trigger for {service_name}')
            db.session.add(new_dc)
            db.session.commit()
            print(f"DEBUG: Saved new datacenter to database: {dc_name}")

        trigger_name = f"Manual CD Trigger - {service_name} - FCP-prod {dc}"
        new_trigger = create_trigger_payload(
            trigger_name,
            template_trigger,
            worker_config,
            dc,
            None,
            sm_integration_id,
            property_overrides,
            reference_dc
        )
        
        # Debug: Print the trigger payload
        print(f"DEBUG: Trigger payload: {json.dumps(new_trigger, indent=2)}")
        
        # Post the trigger
        result = post_trigger(pipeline_id, new_trigger, iam_token)
        
        if result and result.get('success'):
            trigger_data = result.get('data', {})
            return jsonify({
                'success': True,
                'trigger_id': trigger_data.get('id'),
                'trigger_name': trigger_data.get('name'),
                'message': f'Trigger created successfully for {dc}'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to create trigger') if result else 'Failed to create trigger',
                'trigger_exists': result.get('trigger_exists', False) if result else False,
                'details': result.get('details') if result else None
            })
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})
@app.route('/api/fcp/private-worker-secret-options', methods=['POST'])
def fcp_private_worker_secret_options():
    """List Secrets Manager providers and groups for worker credential selection"""
    try:
        data = request.get_json()
        toolchain_guid = data.get('toolchain_guid')
        provider_id = data.get('provider_id')

        if not toolchain_guid:
            return jsonify({'success': False, 'error': 'toolchain_guid is required'})

        iam_token = get_iam_token()
        if not iam_token:
            return jsonify({'success': False, 'error': 'Failed to get IAM token'})

        providers = get_secrets_manager_providers(toolchain_guid)
        if not providers:
            return jsonify({'success': False, 'error': 'No Secrets Manager providers found in toolchain'})

        response_payload = {
            'success': True,
            'providers': [{'id': provider['id'], 'name': provider['name']} for provider in providers]
        }

        if provider_id:
            provider = next((item for item in providers if item['id'] == provider_id), None)
            if not provider:
                return jsonify({'success': False, 'error': 'Selected provider not found in toolchain'})

            groups_result = get_secret_groups_for_provider(provider, iam_token)
            if not groups_result.get('success'):
                return jsonify(groups_result)

            response_payload['groups'] = groups_result.get('groups', [])

        return jsonify(response_payload)
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})


@app.route('/api/fcp/create-worker-from-secret', methods=['POST'])
def fcp_create_worker_from_secret():
    """Create private worker using selected provider/group/secret name"""
    try:
        data = request.get_json()
        toolchain_guid = data.get('toolchain_guid')
        dc = data.get('dc')
        service_name = data.get('service_name')
        provider_id = data.get('provider_id')
        group_id = data.get('group_id')
        secret_name = data.get('secret_name')

        if not all([toolchain_guid, dc, service_name, provider_id, group_id, secret_name]):
            return jsonify({'success': False, 'error': 'toolchain_guid, dc, service_name, provider_id, group_id, and secret_name are required'})

        iam_token = get_iam_token()
        if not iam_token:
            return jsonify({'success': False, 'error': 'Failed to get IAM token'})

        providers = get_secrets_manager_providers(toolchain_guid)
        provider = next((item for item in providers if item['id'] == provider_id), None)
        if not provider:
            return jsonify({'success': False, 'error': 'Selected provider not found in toolchain'})

        secret_result = find_secret_by_name(provider, group_id, secret_name, iam_token)
        if not secret_result.get('success'):
            return jsonify(secret_result)

        secret_crn = secret_result['secret'].get('crn')
        if not secret_crn:
            return jsonify({'success': False, 'error': 'Selected secret does not contain a CRN'})

        payload_result = fetch_secret_payload_from_crn(secret_crn, iam_token)
        if not payload_result.get('success'):
            return jsonify(payload_result)

        worker_name = f"fcp-{dc}-nettools-cd-worker-{normalize_service_name(service_name)}"
        payload = {
            'tool_type_id': 'private_worker',
            'name': worker_name,
            'parameters': {
                'name': worker_name,
                'worker_queue_credentials': payload_result['credentials']
            }
        }

        response = requests.post(
            f'https://api.us-south.devops.cloud.ibm.com/toolchain/v2/toolchains/{toolchain_guid}/tools',
            headers={
                'Authorization': f'Bearer {iam_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            json=payload,
            timeout=60
        )

        if response.status_code not in (200, 201):
            return jsonify({
                'success': False,
                'error': f'Failed to create private worker ({response.status_code})',
                'details': response.text[:1000]
            })

        worker_data = response.json()
        worker_id = worker_data.get('id') or worker_data.get('tool_id') or worker_data.get('instance_id')
        if not worker_id:
            refreshed_worker = get_worker_config(toolchain_guid, iam_token, dc)
            if isinstance(refreshed_worker, dict):
                worker_id = refreshed_worker.get('id')

        return jsonify({
            'success': True,
            'worker': {
                'id': worker_id,
                'name': worker_name
            }
        })
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})


@app.route('/api/fcp/create-trigger-with-worker', methods=['POST'])
def fcp_create_trigger_with_selected_worker():
    """Create trigger with user-selected worker (when multiple workers found)"""
    try:
        data = request.json
        service_name = data.get('service_name')
        dc = data.get('dc')
        worker_id = data.get('worker_id')
        worker_name = data.get('worker_name')
        
        if not all([service_name, dc, worker_id, worker_name]):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        # Get IAM token
        iam_token = get_iam_token()
        if not iam_token:
            return jsonify({'success': False, 'error': 'Failed to get IAM token'})
        
        # Get toolchain GUID
        toolchain_guid = get_toolchain_guid(service_name, iam_token)
        if not toolchain_guid:
            return jsonify({'success': False, 'error': f'Toolchain not found for service: {service_name}'})
        
        # Get pipeline ID
        pipeline_id = get_pipeline_id(toolchain_guid, iam_token)
        if not pipeline_id:
            return jsonify({'success': False, 'error': 'Failed to get pipeline ID'})
        
        # Use the selected worker
        worker_config = {
            'id': worker_id,
            'name': worker_name
        }
        
        # Save DC to database for persistence
        dc_name = dc.lower().strip()
        existing_dc = Datacenter.query.filter_by(name=dc_name).first()
        if not existing_dc:
            new_dc = Datacenter(name=dc_name, description=f'Auto-created from trigger for {service_name}')
            db.session.add(new_dc)
            db.session.commit()
            print(f"DEBUG: Saved new datacenter to database: {dc_name}")
        
        # Get Secrets Manager integration
        sm_integration_id = get_secrets_manager_integration(toolchain_guid, iam_token)
        if not sm_integration_id:
            print("Warning: Secrets Manager integration not found, trigger may fail")
        
        # Create the trigger
        trigger_name = f"Manual CD Trigger - {service_name} - FCP-prod {dc}"
        new_trigger = create_trigger_payload(
            trigger_name,
            None,
            worker_config,
            dc,
            None,
            sm_integration_id
        )
        
        # Post the trigger
        result = post_trigger(pipeline_id, new_trigger, iam_token)
        
        if result:
            return jsonify({
                'success': True,
                'trigger_id': result.get('id'),
                'trigger_name': result.get('name'),
                'message': f'Trigger created successfully for {dc} using worker {worker_name}'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create trigger'})
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})


        worker_data = response.json()
        worker_id = worker_data.get('id') or worker_data.get('tool_id') or worker_data.get('instance_id')
        if not worker_id:
            refreshed_worker = get_worker_config(toolchain_guid, iam_token, dc)
            if isinstance(refreshed_worker, dict):
                worker_id = refreshed_worker.get('id')

        return jsonify({
            'success': True,
            'worker': {
                'id': worker_id,
                'name': worker_name
            }
        })
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})


@app.route('/api/fcp/check-dc-files', methods=['POST'])
def check_dc_files():
    """Check if DC deployment files exist in GitHub repo"""
    try:
        data = request.json
        dc = data.get('dc')
        service_name = data.get('service_name')
        github_token = data.get('github_token')
        
        if not dc or not service_name:
            return jsonify({'success': False, 'error': 'DC and service_name parameters required'})
        
        base_service = normalize_service_name(service_name)
        files_repo = resolve_dc_files_repo_name(service_name)
        
        # Get GitHub token from environment or request
        token = github_token or os.getenv('GITHUB_TOKEN')
        
        if not token:
            return jsonify({
                'success': False,
                'needs_token': True,
                'error': 'GitHub token required. Please provide GITHUB_TOKEN.'
            })
        
        # GitHub API URLs
        repo_owner = 'nettools'
        repo_name = files_repo
        branch = 'fcp-develop'
        
        deployment_file, values_file = build_dc_file_names(dc)
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Check deployment file
        deployment_url = f'https://github.ibm.com/api/v3/repos/{repo_owner}/{repo_name}/contents/kubernetes/{deployment_file}?ref={branch}'
        deployment_response = requests.get(deployment_url, headers=headers, verify=True)
        deployment_exists = deployment_response.status_code == 200
        
        # Check values file
        values_url = f'https://github.ibm.com/api/v3/repos/{repo_owner}/{repo_name}/contents/kubernetes/{values_file}?ref={branch}'
        values_response = requests.get(values_url, headers=headers, verify=True)
        values_exists = values_response.status_code == 200
        
        return jsonify({
            'success': True,
            'dc': dc,
            'service': files_repo,
            'files': {
                'deployment': {
                    'name': deployment_file,
                    'exists': deployment_exists,
                    'url': f'https://github.ibm.com/{repo_owner}/{repo_name}/blob/{branch}/kubernetes/{deployment_file}'
                },
                'values': {
                    'name': values_file,
                    'exists': values_exists,
                    'url': f'https://github.ibm.com/{repo_owner}/{repo_name}/blob/{branch}/kubernetes/{values_file}'
                }
            },
            'all_exist': deployment_exists and values_exists,
            'repo_url': f'https://github.ibm.com/{repo_owner}/{repo_name}/tree/{branch}/kubernetes'
        })
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})

@app.route('/api/fcp/generate-dc-files', methods=['POST'])
def generate_dc_files():
    """Generate DC deployment files from an existing repo template via GitHub API"""
    try:
        data = request.json
        dc = data.get('dc')
        service_name = data.get('service_name')
        github_token = data.get('github_token')
        
        if not dc or not service_name:
            return jsonify({'success': False, 'error': 'DC and service_name parameters required'})
        
        dc = dc.lower().strip()
        base_service = normalize_service_name(service_name)
        files_repo = resolve_dc_files_repo_name(service_name)
        
        token = github_token or os.getenv('GITHUB_TOKEN')
        if not token:
            return jsonify({
                'success': False,
                'needs_token': True,
                'error': 'GitHub token required'
            })
        
        repo_owner = 'nettools'
        repo_name = files_repo
        branch = 'fcp-develop'
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        target_deployment_file, target_values_file = build_dc_file_names(dc)

        requested_source_dc = (data.get('source_dc') or '').lower().strip()
        if requested_source_dc and requested_source_dc != dc:
            candidate_source_dcs = [requested_source_dc]
        else:
            candidate_source_dcs = [
                'dal09', 'dal14', 'che01', 'fra05', 'lon02', 'lon04', 'lon05', 'lon06',
                'mad02', 'mad04', 'osa21', 'osa22', 'osa23', 'sao01', 'sao04', 'sao05',
                'sjc04', 'sng01', 'syd04', 'syd05', 'tok02', 'tok04', 'tor01', 'tor04',
                'tor05', 'wdc04'
            ]
            seen = set()
            candidate_source_dcs = [
                source for source in candidate_source_dcs
                if not (source in seen or seen.add(source)) and source != dc
            ]

        import base64

        selected_source_dc = None
        deployment_content = None
        values_content = None

        for source_dc in candidate_source_dcs:
            source_deployment_file, source_values_file = build_dc_file_names(source_dc)

            deployment_url = f'https://github.ibm.com/api/v3/repos/{repo_owner}/{repo_name}/contents/kubernetes/{source_deployment_file}?ref={branch}'
            values_url = f'https://github.ibm.com/api/v3/repos/{repo_owner}/{repo_name}/contents/kubernetes/{source_values_file}?ref={branch}'

            deployment_response = requests.get(deployment_url, headers=headers, verify=True)
            values_response = requests.get(values_url, headers=headers, verify=True)

            if deployment_response.status_code == 200 and values_response.status_code == 200:
                selected_source_dc = source_dc
                deployment_content = base64.b64decode(deployment_response.json()['content']).decode('utf-8')
                values_content = base64.b64decode(values_response.json()['content']).decode('utf-8')
                break
        
        if not selected_source_dc:
            return jsonify({
                'success': False,
                'needs_reference_dc': not bool(requested_source_dc),
                'dc': dc,
                'service': files_repo,
                'error': (
                    f'Reference DC {requested_source_dc} not found in {repo_name} repo'
                    if requested_source_dc else
                    f'No template DC files found in {repo_name} repo'
                ),
                'checked_source_dcs': candidate_source_dcs
            })
        
        deployment_content = deployment_content.replace(selected_source_dc, dc)
        deployment_content = deployment_content.replace(f'{selected_source_dc}01', f'{dc}01')
        
        values_content = values_content.replace(selected_source_dc, dc)
        values_content = values_content.replace(f'{selected_source_dc}01', f'{dc}01')
        
        runtime_values = build_dc_runtime_values(dc)
        source_runtime_values = build_dc_runtime_values(selected_source_dc)
        for key, source_value in source_runtime_values.items():
            deployment_content = deployment_content.replace(source_value, runtime_values[key])
            values_content = values_content.replace(source_value, runtime_values[key])
        
        return jsonify({
            'success': True,
            'dc': dc,
            'service': files_repo,
            'source_dc': selected_source_dc,
            'files': {
                'deployment': {
                    'name': target_deployment_file,
                    'content': deployment_content
                },
                'values': {
                    'name': target_values_file,
                    'content': values_content
                }
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})

@app.route('/api/fcp/save-dc-files', methods=['POST'])
def save_dc_files():
    """Save DC deployment files to service repo on fcp-develop and create inventory branch fcp-<dc>01 from fcp-dev"""
    try:
        data = request.json
        dc = data.get('dc')
        service_name = data.get('service_name')
        deployment_content = data.get('deployment_content')
        values_content = data.get('values_content')
        github_token = data.get('github_token')
        inventory_source_branch = (data.get('source_branch') or 'fcp-dev').strip()
        inventory_target_branch = (data.get('target_branch') or f'fcp-{dc}01').strip()
        service_branch = 'fcp-develop'

        if not all([dc, service_name, deployment_content, values_content]):
            return jsonify({'success': False, 'error': 'Missing required parameters'})

        service_repo = resolve_dc_files_repo_name(service_name)
        inventory_repo = resolve_inventory_repo_name(service_name)

        token = github_token or os.getenv('GITHUB_TOKEN')
        if not token:
            return jsonify({
                'success': False,
                'needs_token': True,
                'error': 'GitHub token required'
            })

        repo_owner = 'nettools'
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        deployment_file, values_file = build_dc_file_names(dc)

        inventory_source_ref_url = f'https://github.ibm.com/api/v3/repos/{repo_owner}/{inventory_repo}/git/ref/heads/{inventory_source_branch}'
        inventory_source_ref_response = requests.get(inventory_source_ref_url, headers=headers, verify=True)
        if inventory_source_ref_response.status_code in [401, 403]:
            return jsonify({
                'success': False,
                'needs_token': True,
                'error': 'GitHub authentication failed while reading inventory source branch'
            })
        if inventory_source_ref_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Failed to find source branch {inventory_source_branch} in {inventory_repo}'
            })

        inventory_source_sha = inventory_source_ref_response.json().get('object', {}).get('sha')
        if not inventory_source_sha:
            return jsonify({
                'success': False,
                'error': f'Unable to resolve source branch SHA for {inventory_source_branch}'
            })

        inventory_target_ref_url = f'https://github.ibm.com/api/v3/repos/{repo_owner}/{inventory_repo}/git/ref/heads/{inventory_target_branch}'
        inventory_target_ref_response = requests.get(inventory_target_ref_url, headers=headers, verify=True)
        if inventory_target_ref_response.status_code in [401, 403]:
            return jsonify({
                'success': False,
                'needs_token': True,
                'error': 'GitHub authentication failed while checking inventory target branch'
            })

        branch_created = False
        if inventory_target_ref_response.status_code == 404:
            create_ref_response = requests.post(
                f'https://github.ibm.com/api/v3/repos/{repo_owner}/{inventory_repo}/git/refs',
                headers=headers,
                json={
                    'ref': f'refs/heads/{inventory_target_branch}',
                    'sha': inventory_source_sha
                },
                verify=True
            )
            if create_ref_response.status_code not in [200, 201]:
                error_message = create_ref_response.json().get('message', 'Unknown error')
                return jsonify({
                    'success': False,
                    'error': f'Failed to create branch {inventory_target_branch} in {inventory_repo}: {error_message}'
                })
            branch_created = True
        elif inventory_target_ref_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Failed to check target branch {inventory_target_branch} in {inventory_repo}'
            })

        service_deployment_check_url = f'https://github.ibm.com/api/v3/repos/{repo_owner}/{service_repo}/contents/kubernetes/{deployment_file}?ref={service_branch}'
        service_values_check_url = f'https://github.ibm.com/api/v3/repos/{repo_owner}/{service_repo}/contents/kubernetes/{values_file}?ref={service_branch}'

        service_deployment_check_response = requests.get(service_deployment_check_url, headers=headers, verify=True)
        service_values_check_response = requests.get(service_values_check_url, headers=headers, verify=True)

        if service_deployment_check_response.status_code in [401, 403] or service_values_check_response.status_code in [401, 403]:
            return jsonify({
                'success': False,
                'needs_token': True,
                'error': 'GitHub authentication failed while saving DC files'
            })

        deployment_exists = service_deployment_check_response.status_code == 200
        values_exists = service_values_check_response.status_code == 200

        if deployment_exists or values_exists:
            return jsonify({
                'success': False,
                'error': f'Files already exist in branch {service_branch} of {service_repo} repo. Please delete them first if you want to recreate.'
            })

        service_repo_path = os.path.join('/Users/sreekanthchityala/nettools', service_repo)
        service_repo_git_url = f'https://github.ibm.com/{repo_owner}/{service_repo}.git'

        def run_git(command, cwd):
            result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'Git command failed')
            return result

        if not os.path.isdir(service_repo_path):
            clone_result = subprocess.run(
                ['git', 'clone', service_repo_git_url, service_repo_path],
                capture_output=True,
                text=True
            )
            if clone_result.returncode != 0:
                return jsonify({
                    'success': False,
                    'error': f'Failed to clone service repo {service_repo}: {clone_result.stderr.strip() or clone_result.stdout.strip()}'
                })

        try:
            run_git(['git', 'fetch', 'origin'], service_repo_path)
            run_git(['git', 'checkout', service_branch], service_repo_path)
            run_git(['git', 'pull', 'origin', service_branch], service_repo_path)
        except Exception as git_error:
            return jsonify({
                'success': False,
                'error': f'Failed to prepare local service repo {service_repo} on {service_branch}: {git_error}'
            })

        kubernetes_dir = os.path.join(service_repo_path, 'kubernetes')
        os.makedirs(kubernetes_dir, exist_ok=True)

        deployment_path = os.path.join(kubernetes_dir, deployment_file)
        values_path = os.path.join(kubernetes_dir, values_file)
        baseline_path = os.path.join(service_repo_path, '.secrets.baseline')
        venv_path = os.path.join(service_repo_path, 'venv')
        venv_python = os.path.join(venv_path, 'bin', 'python3')
        venv_pip = os.path.join(venv_path, 'bin', 'pip')
        detect_secrets_bin = os.path.join(venv_path, 'bin', 'detect-secrets')

        if os.path.exists(deployment_path) or os.path.exists(values_path):
            return jsonify({
                'success': False,
                'error': f'Files already exist in local branch {service_branch} of {service_repo} repo. Please delete them first if you want to recreate.'
            })

        with open(deployment_path, 'w', encoding='utf-8') as deployment_handle:
            deployment_handle.write(deployment_content)
        with open(values_path, 'w', encoding='utf-8') as values_handle:
            values_handle.write(values_content)

        try:
            subprocess.run(['python3', '-m', 'venv', 'venv'], cwd=service_repo_path, check=True, capture_output=True, text=True)
            subprocess.run(
                [venv_pip, 'install', '--upgrade', 'git+https://github.com/ibm/detect-secrets.git@master#egg=detect-secrets'],
                cwd=service_repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            if os.path.exists(baseline_path):
                subprocess.run(
                    [detect_secrets_bin, 'scan', '--update', '.secrets.baseline'],
                    cwd=service_repo_path,
                    check=True,
                    capture_output=True,
                    text=True
                )
            else:
                baseline_result = subprocess.run(
                    [detect_secrets_bin, 'scan'],
                    cwd=service_repo_path,
                    check=True,
                    capture_output=True,
                    text=True
                )
                with open(baseline_path, 'w', encoding='utf-8') as baseline_handle:
                    baseline_handle.write(baseline_result.stdout)
        except Exception as detect_error:
            return jsonify({
                'success': False,
                'error': f'Failed to run detect-secrets in {service_repo}: {detect_error}'
            })

        try:
            run_git(['git', 'add', f'kubernetes/{deployment_file}', f'kubernetes/{values_file}', '.secrets.baseline'], service_repo_path)
            status_result = run_git(['git', 'status', '--short'], service_repo_path)
            if not status_result.stdout.strip():
                return jsonify({
                    'success': False,
                    'error': f'No local changes detected in {service_repo} after writing files and updating .secrets.baseline'
                })

            commit_message = f'Add {dc} DC YAML files and update detect-secrets baseline'
            run_git(['git', 'commit', '-m', commit_message], service_repo_path)
            run_git(['git', 'push', 'origin', service_branch], service_repo_path)
        except Exception as commit_error:
            return jsonify({
                'success': False,
                'error': f'Failed to commit/push service repo changes for {service_repo}: {commit_error}'
            })

        print(f"Created files locally and pushed for DC {dc} on branch {service_branch}:")
        print(f"  - {deployment_file}")
        print(f"  - {values_file}")
        print(f"Updated detect-secrets baseline in {service_repo_path}")
        print(f"Ensured inventory branch exists: {inventory_repo}:{inventory_target_branch}")

        return jsonify({
            'success': True,
            'message': f'Files created successfully in {service_repo} repo for {dc} on branch {service_branch} and detect-secrets baseline updated',
            'branch': {
                'repo': inventory_repo,
                'source': inventory_source_branch,
                'target': inventory_target_branch,
                'created': branch_created
            },
            'files': {
                'deployment': f'https://github.ibm.com/{repo_owner}/{service_repo}/blob/{service_branch}/kubernetes/{deployment_file}',
                'values': f'https://github.ibm.com/{repo_owner}/{service_repo}/blob/{service_branch}/kubernetes/{values_file}',
                'baseline': f'https://github.ibm.com/{repo_owner}/{service_repo}/blob/{service_branch}/.secrets.baseline'
            },
            'local_repo_path': service_repo_path
        })

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

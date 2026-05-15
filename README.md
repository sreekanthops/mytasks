# My Tasks Dashboard 🎯

A professional Python web application for managing tasks, GitHub issues, reminders, dashboard links, and **IBM Cloud DevOps Pipeline Management** with **Voice Assistant** support.

## ✨ Features

### 1. **🚀 Pipelines Manager (IBM Cloud DevOps)**
   - **5-Step Wizard Interface** - intuitive pipeline management
   - **CI/CD Pipeline Support** - manage both Continuous Integration and Continuous Deployment pipelines
   - **Pipeline Type Selection** - choose between CI and CD pipelines
   - **Trigger Existing Pipelines** - execute CI (git/scm) or CD (manual) triggers
   - **Create New Triggers** - automated trigger creation for new services/DCs
   - **Enhanced Parameter Management**:
     - Display ALL parameters (trigger-specific + global pipeline parameters)
     - Organized sections: Trigger Parameters first, Global Parameters after
     - Real-time parameter search functionality
     - Smart filtering and section hiding
     - CD-specific: Auto-display `one-pipeline-config-branch` with default "fcp-classic-pipeline"
     - CI pipelines: All parameters editable, no fixed config branch
   - **DC-Based Color Coding** - visual identification by data center:
     - 🔵 London (lon) - Blue
     - 🟢 Sydney (syd) - Green
     - 🟣 Tokyo (tok) - Purple
     - 🟠 Dallas (dal) - Orange
     - 🔴 Washington (wdc/was) - Red
     - 🟢 Frankfurt (fra) - Dark Green
     - 🔵 Toronto (tor) - Dark Blue
     - 🟣 Osaka (osa) - Pink/Magenta
   - **Direct Pipeline Access** - clickable URL buttons to view pipeline runs
   - **Real-time Status** - monitor pipeline execution and logs
   - **IBM Cloud IAM Integration** - secure authentication with IBM Cloud
   - **Toolchain Search** - find toolchains by service name
   - **Automated Worker Creation** - creates CD workers for new triggers

### 2. **🎤 Voice Assistant**
   - **Always-listening mode** - no wake word needed
   - **Hands-free navigation** - "Open dashboard links"
   - **Smart search** - "Search grafana in prod"
   - **Persistent across pages** - stays active after navigation
   - **Environment-aware** - understands "in prod", "for staging"
   - **Browser-based** - uses built-in speech recognition (Chrome, Edge, Safari)

### 3. **🔔 Smart Notifications**
   - **Urgent task alerts** - desktop notifications for tasks < 24 hours
   - **Reminder notifications** - alerts when reminders are due
   - **Visual indicators** - blinking alerts for urgent items
   - **Snooze functionality** - 15min, 30min, 1hr, or custom
   - **Urgent count badge** - pulsing indicator in sidebar

### 4. **📋 Task Management**
   - Add, update, and delete tasks
   - Task statuses: Pending, In Progress, On Hold, Done, Archive
   - Set deadlines and due dates
   - **Task reminders** - set multiple reminders per task
   - **Urgent detection** - automatic alerts for approaching deadlines
   - Filter tasks by status
   - Link tasks to GitHub issues or Jira tickets

### 5. **🔗 Dashboard Links**
   - Save frequently used links with descriptions
   - **Environment grouping** - organize by prod, staging, dev, etc.
   - **Multiple environments** - assign links to multiple environments
   - **Smart search** - search by name, URL, or description
   - **Edit links** - update existing links easily
   - Quick access to important resources

### 6. **⏰ Reminders**
   - Create time-based reminders
   - View active and urgent reminders
   - Desktop notifications when due
   - Dismiss completed reminders

### 7. **🐙 GitHub Issues Integration**
   - View open/closed GitHub issues from IBM GitHub Enterprise
   - Filter issues by status
   - Direct links to GitHub issues
   - Create tasks from GitHub issues

### 8. **🎫 Jira Integration**
   - View assigned Jira issues from Atlassian Cloud
   - Filter by status: Open, In Progress, Done
   - Priority and type badges
   - Create tasks directly from Jira issues
   - Secure API token authentication

## 📋 Prerequisites

### Required:
- **Python 3.9+** (tested with Python 3.9.17)
- **pip** (Python package manager)
- **PostgreSQL** or **SQLite** (database)
- **Modern web browser** with speech recognition support:
  - ✅ Google Chrome (recommended)
  - ✅ Microsoft Edge
  - ✅ Safari
  - ⚠️ Firefox (limited speech support)

### Optional:
- **IBM Cloud CLI** (for FCP Pipeline Manager)
- **IBM Cloud Account** (for DevOps pipeline access)
- **GitHub Personal Access Token** (for GitHub integration)
- **Jira API Token** (for Jira integration)
- **HTTPS or localhost** (required for microphone access)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd mytasks
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your configuration:
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/mytasks  # or sqlite:///mytasks.db
HOST=127.0.0.1  # Localhost only for security
PORT=5000
```

### 5. Create PostgreSQL Database (if using PostgreSQL)
```bash
# Create database
createdb mytasks

# Or using psql
psql -U postgres
CREATE DATABASE mytasks;
\q
```

### 6. Run Database Migrations
```bash
# Run all migrations
python migrate_mute_until.py
python migrate_task_fields.py
python migrate_task_reminders.py
python migrate_jira_settings.py
```

### 7. Start the Application
```bash
python app.py
```

### 8. Open in Browser
```
http://localhost:5000
```

## 🎤 Voice Assistant Setup

### 1. Enable Microphone Access
- Browser will ask for microphone permission
- Click **"Allow"** when prompted
- Check browser settings if permission was denied

### 2. Activate Voice Assistant
- Click the **"Voice Assistant"** button in the sidebar (bottom)
- Button turns **green** when active
- Now just speak your commands!

### 3. Voice Commands

#### Navigation (no wake word needed):
```
"Open dashboard links"
"Open tasks"
"Show reminders"
"Open GitHub"
"Open settings"
"Go to dashboard"
```

#### Search with Environment:
```
"Search grafana"
"Search grafana in prod"
"Search grafana for staging"
"Search kibana in production"
```

#### Create Items:
```
"Create new task"
"Add new reminder"
"Create new link"
```

### 4. Turn Off Voice Assistant
- Click the **"Voice Assistant"** button again (turns gray)
- Or close the browser tab

## ⚙️ Configuration

### Pipelines Manager (IBM Cloud DevOps)
1. **Install IBM Cloud CLI**:
   ```bash
   # macOS
   curl -fsSL https://clis.cloud.ibm.com/install/osx | sh
   
   # Linux
   curl -fsSL https://clis.cloud.ibm.com/install/linux | sh
   ```

2. **Login to IBM Cloud**:
   ```bash
   ibmcloud login --sso
   ```

3. **Access Pipelines Manager**:
   - Navigate to **Pipelines** in the sidebar
   - The wizard will guide you through:
     - **Step 1**: Choose mode (Trigger or Create)
     - **Step 1.5**: Select pipeline type (CI or CD) - for Trigger mode
     - **Step 2**: Enter service name
     - **Step 3**: Select toolchain and triggers
     - **Step 4**: Configure parameters (with search)
     - **Step 5**: Execute and monitor

### GitHub Integration
1. Navigate to **Settings** in the dashboard
2. Enter your GitHub username (e.g., `Sreekanth-Chityala`)
3. Enter your GitHub Personal Access Token
   - For IBM GitHub Enterprise: https://github.ibm.com/settings/tokens
   - Required scopes: `repo` (for accessing issues)

### Jira Integration
1. Navigate to **Settings** in the dashboard
2. Configure Jira settings:
   - **Jira URL**: Your Atlassian domain (e.g., `https://your-domain.atlassian.net`)
   - **Email**: Your Jira account email
   - **API Token**: Generate from https://id.atlassian.com/manage-profile/security/api-tokens
   - **Project Key**: Default project key (e.g., `PROJ`)

### Environment Management
1. Go to **Dashboard Links** page
2. Click **"Manage Environments"**
3. Add environments (e.g., Production, Staging, Development)
4. Assign colors for visual identification

## 📊 Database

The application supports both **PostgreSQL** (recommended) and **SQLite**.

### Database Tables:
- `task` - User tasks with deadlines, reminders, and GitHub/Jira links
- `reminder` - Time-based reminders
- `dashboard_link` - Saved links with environment grouping
- `environment` - Environment definitions (prod, staging, etc.)
- `settings` - GitHub and Jira configuration
- `task_reminder` - Task-specific reminders

### PostgreSQL (Recommended):
```bash
# Create database
createdb mytasks

# Set in .env
DATABASE_URL=postgresql://user:password@localhost:5432/mytasks
```

### SQLite (Development):
```bash
# Set in .env
DATABASE_URL=sqlite:///mytasks.db
```

## 🎯 Usage Guide

### Pipelines Manager
1. **Navigate to Pipelines** in the sidebar
2. **Choose Mode**:
   - **Trigger Existing**: Execute existing CI or CD pipelines
   - **Create New**: Create new triggers for services/DCs
3. **Select Pipeline Type** (for Trigger mode):
   - **CI Pipeline**: Continuous Integration (git/scm triggers)
   - **CD Pipeline**: Continuous Deployment (manual triggers)
4. **Enter Service Name**: e.g., "log-alerts", "network-monitoring" (case-insensitive)
5. **Select Toolchain**: Choose from search results (filtered by CI/CD type)
6. **Select Trigger(s)**:
   - Color-coded by DC (London=Blue, Sydney=Green, etc.)
   - Filtered by pipeline type
7. **Configure Parameters**:
   - View ALL parameters (trigger-specific + global)
   - Use search box to find specific parameters
   - Parameters organized in sections
   - CD: `one-pipeline-config-branch` shown (default: "fcp-classic-pipeline")
   - CI: All parameters editable
8. **Execute**:
   - Click "Execute"
   - Get direct URL to pipeline run
   - Monitor status and logs in real-time

### Tasks
1. Click **"New Task"** button
2. Fill in:
   - Title (required)
   - Description
   - Status (Pending, In Progress, On Hold, Done, Archive)
   - Priority (Low, Medium, High, Urgent)
   - Deadline (for urgent alerts)
   - Due Date
   - GitHub Issue (optional)
3. Click **"Add Task"**
4. Set reminders using the 🔔 button on each task
5. Snooze urgent tasks using snooze buttons

### Dashboard Links
1. Click **"New Link"** button
2. Fill in:
   - Name (required)
   - URL (required)
   - Description (optional)
   - Environment(s) - select multiple
3. Use search bar to filter links
4. Edit links using the ✏️ button
5. Links are grouped by environment

### Reminders
1. Click **"New Reminder"** button
2. Set:
   - Title
   - Description
   - Reminder time
3. Desktop notifications appear when due
4. Urgent tasks (< 24 hours) appear automatically

### GitHub Issues
1. Configure GitHub token in **Settings**
2. Navigate to **GitHub** page
3. View open/closed issues
4. Create tasks directly from issues
5. Click issue links to open in GitHub

### Jira Issues
1. Configure Jira settings in **Settings**
2. Navigate to **Jira** page
3. View assigned issues
4. Filter by status
5. Create tasks from Jira issues

## 🛠️ Technology Stack

- **Backend**: Flask 3.0.0 (Python 3.9+)
- **Database**: SQLAlchemy with PostgreSQL/SQLite
- **ORM**: Flask-SQLAlchemy 3.1.1
- **HTTP Client**: Requests 2.31.0
- **PostgreSQL Driver**: psycopg2-binary 2.9.9
- **WSGI Server**: Gunicorn 21.2.0 (production)
- **Environment**: python-dotenv 1.0.0
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Icons**: Font Awesome 6.4.0
- **Speech**: Web Speech API (browser built-in)
- **Notifications**: Web Notifications API
- **IBM Cloud**: IBM Cloud CLI, DevOps API v2

## 📁 Project Structure

```
mytasks/
├── app.py                          # Flask application and API routes
├── requirements.txt                # Python dependencies (6 packages)
├── runtime.txt                     # Python version (3.9.17)
├── Procfile                        # Heroku deployment config
├── wsgi.py                         # WSGI entry point
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
├── README.md                       # This file
├── USER_GUIDE.md                   # Detailed user guide
├── DEPLOYMENT.md                   # Deployment instructions
├── QUICK_DEPLOY.md                 # Quick deployment guide
├── migrate_*.py                    # Database migration scripts
│   ├── migrate_db.py               # Initial database setup
│   ├── migrate_mute_until.py       # Add mute/snooze fields
│   ├── migrate_task_fields.py      # Add task fields
│   ├── migrate_task_reminders.py   # Add task reminders
│   └── migrate_jira_settings.py    # Add Jira configuration
├── templates/
│   ├── base.html                   # Base template with sidebar
│   ├── tasks.html                  # Tasks page
│   ├── reminders.html              # Reminders page
│   ├── links.html                  # Dashboard links page
│   ├── github.html                 # GitHub issues page
│   ├── jira.html                   # Jira issues page
│   ├── fcp_wizard.html             # FCP Pipeline Manager (5-step wizard)
│   ├── settings.html               # Settings page
│   └── modals/                     # Modal dialogs
│       ├── task_modal.html
│       ├── reminder_modal.html
│       ├── link_modal.html
│       ├── env_modal.html
│       └── task_reminder_modal.html
├── static/
│   ├── css/
│   │   └── style.css               # Main stylesheet with FCP styling
│   └── js/
│       ├── common.js               # Shared functions
│       ├── tasks.js                # Tasks page logic
│       ├── reminders.js            # Reminders page logic
│       ├── links.js                # Links page logic
│       ├── github.js               # GitHub integration
│       ├── settings.js             # Settings page logic
│       ├── fcp-wizard.js           # FCP Pipeline Manager logic
│       └── voice-assistant.js      # Voice assistant
└── mytasks.db                      # SQLite database (auto-generated)
```

## 🔌 API Endpoints

### Pipelines Manager
- `GET /fcp/wizard` - Pipelines Manager wizard page
- `POST /api/fcp/search-toolchains` - Search toolchains by service name (supports pipeline_type: ci/cd)
- `POST /api/fcp/get-triggers` - Get triggers for a toolchain (filtered by pipeline_type)
- `POST /api/fcp/get-trigger-properties` - Get trigger and global properties for editing
- `POST /api/fcp/trigger-pipeline` - Trigger pipeline with property overrides
- `POST /api/fcp/create-trigger` - Create new trigger for service/DC
- `POST /api/fcp/pipeline-status` - Get pipeline run status and logs
- `GET /api/fcp/check-auth` - Check IBM Cloud authentication
- `POST /api/fcp/open-terminal` - Open terminal with pipeline script

### Tasks
- `GET /api/tasks?status=<status>` - Get tasks
- `POST /api/tasks` - Create task
- `PUT /api/tasks/<id>` - Update task
- `DELETE /api/tasks/<id>` - Delete task
- `GET /api/tasks/urgent-count` - Get urgent task count
- `POST /api/tasks/<id>/snooze` - Snooze urgent task

### Task Reminders
- `GET /api/task-reminders/<task_id>` - Get task reminders
- `POST /api/task-reminders` - Create task reminder
- `DELETE /api/task-reminders/<id>` - Delete task reminder

### Reminders
- `GET /api/reminders` - Get reminders
- `POST /api/reminders` - Create reminder
- `DELETE /api/reminders/<id>` - Delete reminder

### Links
- `GET /api/links?environment_id=<id>` - Get links
- `POST /api/links` - Create link
- `GET /api/links/<id>` - Get single link
- `PUT /api/links/<id>` - Update link
- `DELETE /api/links/<id>` - Delete link

### Environments
- `GET /api/environments` - Get environments
- `POST /api/environments` - Create environment
- `DELETE /api/environments/<id>` - Delete environment

### GitHub
- `GET /api/github/issues?status=<open|closed|all>` - Fetch issues

### Jira
- `GET /api/jira/issues?status=<open|inprogress|done|all>` - Fetch Jira issues

### Settings
- `GET /api/settings` - Get settings (GitHub + Jira)
- `POST /api/settings` - Save settings

## 🔒 Security

### ✅ Security Features
- **Environment Variables**: Sensitive data in `.env` (not committed)
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **API Token Storage**: Encrypted in database (GitHub, Jira, IBM Cloud)
- **HTTPS**: All external API calls use `verify=True`
- **Local Binding**: Runs on `127.0.0.1` (localhost only)
- **Session Security**: SECRET_KEY for session encryption
- **No External Dependencies**: Voice processing is browser-based

### 📦 Package Security
All Python packages are:
- ✅ Latest stable versions (as of 2023-2024)
- ✅ No known CVEs (Common Vulnerabilities)
- ✅ Actively maintained
- ✅ Production-ready

```
Flask==3.0.0              ✅ Latest stable
Flask-SQLAlchemy==3.1.1   ✅ Latest stable
requests==2.31.0          ✅ Secure version
psycopg2-binary==2.9.9    ✅ Latest stable
gunicorn==21.2.0          ✅ Production WSGI
python-dotenv==1.0.0      ✅ Environment management
```

### 🛡️ Security Recommendations
1. **Use PostgreSQL in production** (not SQLite)
2. **Set strong SECRET_KEY** in `.env`
3. **Run on localhost** (`127.0.0.1`) for personal use
4. **Use HTTPS** if exposing to network
5. **Rotate API tokens** periodically
6. **Keep packages updated**: `pip list --outdated`
7. **IBM Cloud IAM**: Use SSO authentication
8. **Database backups**: Regular backups of PostgreSQL

### ⚠️ Security Impact: MINIMAL
- Application is for **personal/local use**
- Runs on **localhost only** (not exposed to internet)
- Behind **IBM corporate firewall** (if applicable)
- **Single user** application
- **No public-facing endpoints**

## 🚀 Deployment

### Heroku
```bash
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DATABASE_URL=your-postgres-url

# Deploy
git push heroku main

# Run migrations
heroku run python migrate_mute_until.py
```

### Local Production
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn wsgi:app -b 0.0.0.0:5000
```

## 🐛 Troubleshooting

### Pipelines Manager Issues
- **IBM Cloud CLI not found**: Install IBM Cloud CLI
- **Authentication failed**: Run `ibmcloud login --sso`
- **Toolchain not found**: Verify service name spelling (case-insensitive search)
- **No CI/CD toolchains found**: Check if service has -ci or -cd toolchains
- **No triggers found**: Verify pipeline type selection (CI vs CD)
- **Trigger creation failed**: Check IAM permissions
- **Pipeline URL not working**: Verify you have access to the toolchain
- **Parameters not showing**: Check browser console for errors
- **Search not working**: Clear browser cache and reload

### Voice Assistant Not Working
- **Check browser**: Use Chrome, Edge, or Safari
- **Check permissions**: Allow microphone access in browser settings
- **Check HTTPS**: Voice recognition requires HTTPS or localhost
- **Check console**: Open F12 → Console for error messages

### Database Issues
- **PostgreSQL connection failed**:
  ```bash
  # Check if PostgreSQL is running
  pg_isready
  
  # Create database if missing
  createdb mytasks
  ```
- **Run all migrations**:
  ```bash
  python migrate_db.py
  python migrate_mute_until.py
  python migrate_task_fields.py
  python migrate_task_reminders.py
  python migrate_jira_settings.py
  ```
- **Reset database**:
  ```bash
  # PostgreSQL
  dropdb mytasks && createdb mytasks
  
  # SQLite
  rm mytasks.db
  ```
- **Check permissions**: Ensure write access to database file

### GitHub Integration Issues
- **Check token**: Verify token has `repo` scope
- **Check username**: Ensure correct GitHub username (e.g., `Sreekanth-Chityala`)
- **Check network**: Verify access to GitHub API
- **IBM GitHub Enterprise**: Use `https://github.ibm.com` URL

### Jira Integration Issues
- **Authentication failed**: Verify API token is correct
- **No issues found**: Check project key and JQL query
- **Connection timeout**: Verify Jira URL (include `https://`)
- **API token**: Generate from https://id.atlassian.com/manage-profile/security/api-tokens

## 📝 Future Enhancements

### Pipelines Manager
- [x] CI/CD pipeline type selection
- [x] Enhanced parameter display with search
- [x] Case-insensitive service search
- [ ] Pipeline run history and analytics
- [ ] Bulk trigger creation for multiple DCs
- [ ] Pipeline template management
- [ ] Automated rollback on failure
- [ ] Pipeline comparison tool
- [ ] Custom DC color themes
- [ ] CI pipeline creation wizard

### General Features
- [ ] AI-powered task suggestions
- [ ] Email notifications for reminders
- [ ] Task categories and tags
- [ ] Export tasks to CSV/JSON
- [ ] Dark mode toggle
- [ ] Calendar view for tasks and reminders
- [ ] Task collaboration features
- [ ] Mobile app (React Native)
- [ ] Slack/Teams integration
- [ ] Voice command customization
- [ ] Multi-user support with authentication
- [ ] Task dependencies and subtasks
- [ ] Time tracking for tasks
- [ ] Gantt chart view

## 📄 License

MIT License - feel free to use and modify!

## 👤 Author

Sreekanth Chityala

## 🙏 Acknowledgments

- **Flask Framework** - Web application framework
- **SQLAlchemy** - Database ORM
- **Font Awesome** - Icons
- **Web Speech API** - Voice recognition
- **IBM Cloud DevOps** - Pipeline management API
- **PostgreSQL** - Database system
- **Gunicorn** - WSGI server

---

**Made with ❤️ for IBM Cloud DevOps and Task Management**

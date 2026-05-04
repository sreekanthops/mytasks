# My Tasks Dashboard 🎯

A professional Python web application for managing tasks, GitHub issues, reminders, and dashboard links with **Voice Assistant** support.

## ✨ Features

### 1. **🎤 Voice Assistant (NEW!)**
   - **Always-listening mode** - no wake word needed
   - **Hands-free navigation** - "Open dashboard links"
   - **Smart search** - "Search grafana in prod"
   - **Persistent across pages** - stays active after navigation
   - **Environment-aware** - understands "in prod", "for staging"
   - **Browser-based** - uses built-in speech recognition (Chrome, Edge, Safari)

### 2. **🔔 Smart Notifications**
   - **Urgent task alerts** - desktop notifications for tasks < 24 hours
   - **Reminder notifications** - alerts when reminders are due
   - **Visual indicators** - blinking alerts for urgent items
   - **Snooze functionality** - 15min, 30min, 1hr, or custom
   - **Urgent count badge** - pulsing indicator in sidebar

### 3. **📋 Task Management**
   - Add, update, and delete tasks
   - Task statuses: Pending, In Progress, On Hold, Done, Archive
   - Set deadlines and due dates
   - **Task reminders** - set multiple reminders per task
   - **Urgent detection** - automatic alerts for approaching deadlines
   - Filter tasks by status

### 4. **🔗 Dashboard Links**
   - Save frequently used links with descriptions
   - **Environment grouping** - organize by prod, staging, dev, etc.
   - **Multiple environments** - assign links to multiple environments
   - **Smart search** - search by name, URL, or description
   - **Edit links** - update existing links easily
   - Quick access to important resources

### 5. **⏰ Reminders**
   - Create time-based reminders
   - View active and urgent reminders
   - Desktop notifications when due
   - Dismiss completed reminders

### 6. **🐙 GitHub Issues Integration**
   - View open/closed GitHub issues from IBM GitHub Enterprise
   - Filter issues by status
   - Direct links to GitHub issues

## 📋 Prerequisites

### Required:
- **Python 3.8+**
- **pip** (Python package manager)
- **Modern web browser** with speech recognition support:
  - ✅ Google Chrome (recommended)
  - ✅ Microsoft Edge
  - ✅ Safari
  - ⚠️ Firefox (limited speech support)

### Optional:
- **GitHub Personal Access Token** (for GitHub integration)
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
# SECRET_KEY=your-secret-key-here
# DATABASE_URL=sqlite:///mytasks.db  # or PostgreSQL URL for production
```

### 5. Run Database Migration (if needed)
```bash
python migrate_mute_until.py
```

### 6. Start the Application
```bash
python app.py
```

### 7. Open in Browser
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

### GitHub Integration
1. Navigate to **Settings** in the dashboard
2. Enter your GitHub username (e.g., `Sreekanth-Chityala`)
3. Enter your GitHub Personal Access Token
   - For IBM GitHub Enterprise: https://github.ibm.com/settings/tokens
   - Required scopes: `repo` (for accessing issues)

### Environment Management
1. Go to **Dashboard Links** page
2. Click **"Manage Environments"**
3. Add environments (e.g., Production, Staging, Development)
4. Assign colors for visual identification

## 📊 Database

The application uses **SQLite** by default (`mytasks.db`), automatically created on first run.

### Database Tables:
- `task` - User tasks with deadlines and reminders
- `reminder` - Time-based reminders
- `dashboard_link` - Saved links with environment grouping
- `environment` - Environment definitions (prod, staging, etc.)
- `settings` - GitHub configuration
- `task_reminder` - Task-specific reminders

### PostgreSQL (Production):
Set `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql://user:password@localhost/mytasks
```

## 🎯 Usage Guide

### Tasks
1. Click **"New Task"** button
2. Fill in:
   - Title (required)
   - Description
   - Status (Pending, In Progress, On Hold, Done, Archive)
   - Priority (Low, Medium, High, Urgent)
   - Deadline (for urgent alerts)
   - Due Date
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

## 🛠️ Technology Stack

- **Backend**: Flask (Python 3.8+)
- **Database**: SQLAlchemy with SQLite/PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Icons**: Font Awesome 6.4.0
- **Speech**: Web Speech API (browser built-in)
- **Notifications**: Web Notifications API

## 📁 Project Structure

```
mytasks/
├── app.py                          # Flask application and API routes
├── requirements.txt                # Python dependencies
├── runtime.txt                     # Python version for Heroku
├── Procfile                        # Heroku deployment config
├── wsgi.py                         # WSGI entry point
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
├── README.md                       # This file
├── migrate_*.py                    # Database migration scripts
├── templates/
│   ├── base.html                   # Base template with sidebar
│   ├── dashboard.html              # Main dashboard (deprecated)
│   ├── tasks.html                  # Tasks page
│   ├── reminders.html              # Reminders page
│   ├── links.html                  # Dashboard links page
│   ├── github.html                 # GitHub issues page
│   ├── settings.html               # Settings page
│   └── modals/                     # Modal dialogs
│       ├── task_modal.html
│       ├── reminder_modal.html
│       ├── link_modal.html
│       ├── env_modal.html
│       └── task_reminder_modal.html
├── static/
│   ├── css/
│   │   └── style.css               # Main stylesheet
│   └── js/
│       ├── common.js               # Shared functions
│       ├── tasks.js                # Tasks page logic
│       ├── reminders.js            # Reminders page logic
│       ├── links.js                # Links page logic
│       ├── github.js               # GitHub integration
│       ├── settings.js             # Settings page logic
│       └── voice-assistant.js      # Voice assistant (NEW!)
└── mytasks.db                      # SQLite database (auto-generated)
```

## 🔌 API Endpoints

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

### Settings
- `GET /api/settings` - Get settings
- `POST /api/settings` - Save settings

## 🔒 Security Notes

- GitHub tokens are stored encrypted in the database
- `SECRET_KEY` should be set in `.env` for production
- `.env` file is excluded from git (in `.gitignore`)
- For production, use HTTPS and a proper WSGI server (gunicorn)
- Consider adding authentication for multi-user scenarios
- Voice commands are processed locally (no external API calls)

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

### Voice Assistant Not Working
- **Check browser**: Use Chrome, Edge, or Safari
- **Check permissions**: Allow microphone access in browser settings
- **Check HTTPS**: Voice recognition requires HTTPS or localhost
- **Check console**: Open F12 → Console for error messages

### Database Issues
- **Run migrations**: `python migrate_mute_until.py`
- **Reset database**: Delete `mytasks.db` and restart app
- **Check permissions**: Ensure write access to database file

### GitHub Integration Issues
- **Check token**: Verify token has `repo` scope
- **Check username**: Ensure correct GitHub username
- **Check network**: Verify access to GitHub API

## 📝 Future Enhancements

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

## 📄 License

MIT License - feel free to use and modify!

## 👤 Author

Sreekanth Chityala

## 🙏 Acknowledgments

- Flask framework
- Font Awesome icons
- Web Speech API
- SQLAlchemy ORM

---

**Made with ❤️ and 🎤 Voice Control**

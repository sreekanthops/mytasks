# My Tasks Dashboard

A professional Python web application for managing tasks, GitHub issues, reminders, and dashboard links.

## Features

1. **GitHub Issues Integration**
   - View open/closed GitHub issues from IBM GitHub Enterprise
   - Filter issues by status
   - Direct links to GitHub issues

2. **Task Management**
   - Add, update, and delete tasks
   - Task statuses: Pending, In Progress, On Hold, Done, Archive
   - Set due dates for tasks
   - Filter tasks by status

3. **Reminders**
   - Create time-based reminders
   - View active reminders
   - Dismiss completed reminders

4. **Dashboard Links**
   - Save frequently used links
   - Search links by name
   - Quick access to important resources

## Installation

1. Install dependencies:
```bash
cd /Users/sreekanthchityala/nettools/mytasks
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Configuration

1. Navigate to the Settings section in the dashboard
2. Enter your GitHub username (e.g., Sreekanth-Chityala)
3. Enter your GitHub Personal Access Token
   - For IBM GitHub Enterprise, generate a token at: https://github.ibm.com/settings/tokens
   - Required scopes: `repo` (for accessing issues)

## Database

The application uses SQLite database (`mytasks.db`) which is automatically created on first run.

Database tables:
- `task` - Stores user tasks
- `reminder` - Stores reminders
- `dashboard_link` - Stores dashboard links
- `settings` - Stores GitHub configuration

## Usage

### GitHub Issues
1. Configure your GitHub token in Settings
2. Navigate to GitHub Issues section
3. Select status filter (Open/Closed/All)
4. Click Refresh to load issues

### Tasks
1. Click "Add Task" button
2. Fill in task details (title, description, status, due date)
3. Update task status using the dropdown in each task card
4. Delete tasks using the trash icon

### Reminders
1. Click "Add Reminder" button
2. Set reminder title, description, and time
3. Dismiss reminders when completed

### Dashboard Links
1. Click "Add Link" button
2. Enter link name, URL, and optional description
3. Search links using the search box
4. Click on any link card to open in new tab

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy with SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Icons**: Font Awesome
- **API Integration**: GitHub REST API

## Project Structure

```
mytasks/
├── app.py                 # Flask application and API routes
├── requirements.txt       # Python dependencies
├── mytasks.db            # SQLite database (auto-generated)
├── templates/
│   └── dashboard.html    # Main dashboard template
├── static/
│   ├── css/
│   │   └── style.css     # Dashboard styles
│   └── js/
│       └── app.js        # Frontend JavaScript
└── README.md             # This file
```

## API Endpoints

- `GET /api/github/issues?status=<open|closed|all>` - Fetch GitHub issues
- `GET /api/tasks?status=<status>` - Get tasks
- `POST /api/tasks` - Create new task
- `PUT /api/tasks/<id>` - Update task
- `DELETE /api/tasks/<id>` - Delete task
- `GET /api/reminders` - Get reminders
- `POST /api/reminders` - Create reminder
- `DELETE /api/reminders/<id>` - Dismiss reminder
- `GET /api/links?search=<query>` - Get links
- `POST /api/links` - Create link
- `DELETE /api/links/<id>` - Delete link
- `GET /api/settings` - Get settings
- `POST /api/settings` - Save settings

## Security Notes

- GitHub tokens are stored in the database (consider encrypting in production)
- Change the `SECRET_KEY` in app.py for production use
- For production deployment, use a proper WSGI server (gunicorn, uWSGI)
- Consider adding authentication for multi-user scenarios

## Future Enhancements

- Email notifications for reminders
- Task categories and tags
- Export tasks to CSV/JSON
- Dark mode toggle
- Calendar view for tasks and reminders
- Task collaboration features
- Mobile responsive improvements# mytasks

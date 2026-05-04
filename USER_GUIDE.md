# MyTasks Dashboard - User Guide

## 🎯 Overview
Professional task management dashboard with GitHub integration, smart deadline reminders, and quick access to daily tools.

## 🚀 Getting Started

### Local Setup
```bash
cd /Users/sreekanthchityala/nettools/mytasks
source venv/bin/activate
python app.py
```
Access at: **http://127.0.0.1:5000**

### First Time Setup
1. Go to **Settings** (⚙️ Configuration in sidebar)
2. Add your **GitHub Token** (for IBM GitHub Enterprise)
3. Add your **GitHub Username** (e.g., Sreekanth-Chityala)
4. Click **Save Settings**

## 📋 Features

### 1. GitHub Issues Integration
- **View Issues**: See all your assigned GitHub issues (open/closed)
- **Import as Task**: Select issue from dropdown when creating task
- **Auto-fill**: Issue title and description automatically populate
- **Direct Link**: Click GitHub badge on task to open issue

**How to use:**
1. Click **+ Add Task**
2. Select GitHub issue from dropdown
3. Title and description auto-fill
4. Set priority and deadline
5. Submit

### 2. Task Management

**Create Task:**
- Title (required)
- Description
- GitHub Issue (optional - select from dropdown)
- Status: Pending, In Progress, On Hold, Done
- Priority: Low 🟢, Medium 🟡, High 🟠, Urgent 🔴
- Deadline (required) - triggers smart reminders
- Due Date (optional)

**Task Card Features:**
- **GitHub Badge**: Purple gradient badge with issue number (clickable)
- **Priority Badge**: Color-coded priority indicator
- **Deadline Badge**: Shows deadline date
- **Status Dropdown**: Quick status change
- **Mute Button**: Bell icon to mute/unmute deadline reminders
- **Delete Button**: Remove task

**Smart Deadline Reminders:**
- **1 week before**: Reminder once per day
- **1 day before**: Reminder every 3 hours
- **Overdue**: Reminder every 3 hours

**Mute Functionality:**
- Click bell icon (🔔) to mute deadline reminders
- Click again (🔕) to unmute
- Muted tasks show "Muted" badge
- Only mutes deadline notifications, not the task itself

### 3. Reminders Section
Create custom one-time reminders:
- Title and description
- Specific date/time
- Desktop notifications with sound
- Browser notifications (requires permission)

**Notification Types:**
- Desktop notification with sound
- In-app toast notification
- Clickable to dismiss

### 4. Dashboard Links
Organize your frequently used links:
- **Add Links**: Name, URL, description
- **Environments**: Group by Production, Staging, Development, etc.
- **Search**: Filter links by name
- **Quick Access**: Click to open in new tab

**Manage Environments:**
1. Click **Manage Environments**
2. Add environment name and color
3. Assign links to environments
4. Filter by environment

### 5. Quick Access Sidebar
One-click access to daily tools:
- 📧 **Email** (Gmail)
- 📅 **Calendar** (Google Calendar)
- ☁️ **Drive** (Google Drive)
- 💬 **Slack**

## 🎨 UI Features

### Beautiful Design
- Gradient purple/blue theme
- Smooth animations
- Card hover effects
- Professional badges
- Responsive layout

### Status Badges
- **Pending**: Yellow badge
- **In Progress**: Blue badge with pulse
- **On Hold**: Gray badge
- **Done**: Green badge
- **Archive**: Dark gray badge

### Priority Colors
- **Low**: Green (#10b981)
- **Medium**: Amber (#f59e0b)
- **High**: Orange (#f97316)
- **Urgent**: Red (#ef4444)

## 🔔 Notification System

### Desktop Notifications
- Requires browser permission (click "Allow" when prompted)
- Sound alerts for reminders
- Clickable notifications
- Persistent for important reminders

### Deadline Reminders
Automatic based on deadline:
- 🟡 **Warning** (1 week): Daily reminder
- 🔴 **Critical** (1 day): Every 3 hours
- ⚠️ **Overdue**: Every 3 hours

### Muting Reminders
- Per-task mute control
- Mutes only deadline notifications
- Toggle on/off anytime
- Visual indicator when muted

## 💾 Database

### PostgreSQL Setup
```bash
# Local database
DATABASE_URL=postgresql://sreekanthchityala@localhost:5432/mytasks

# Tables
- task (tasks with GitHub integration)
- reminder (custom reminders)
- dashboard_link (quick links)
- environment (link categories)
- settings (GitHub configuration)
```

### Backup/Export
```bash
# Export database
pg_dump mytasks > mytasks_backup.sql

# Import to server
psql -U tasks -d mytasks < mytasks_backup.sql
```

## 🔧 Configuration

### Environment Variables (.env)
```
DATABASE_URL=postgresql://user@localhost:5432/mytasks
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
HOST=127.0.0.1
PORT=5000
```

### GitHub Token
- Go to GitHub Settings → Developer Settings → Personal Access Tokens
- Generate token with `repo` scope
- Add to dashboard Settings

## 📱 Keyboard Shortcuts
- **Esc**: Close modal
- **Cmd+Shift+R**: Hard refresh (see latest changes)

## 🐛 Troubleshooting

### GitHub Issues Not Loading
1. Check GitHub token in Settings
2. Verify token has `repo` permissions
3. Check GitHub username is correct
4. For IBM GitHub: Use `https://github.ibm.com` URL

### Notifications Not Working
1. Check browser notification permissions
2. Allow notifications when prompted
3. Check browser settings for site permissions

### Database Issues
```bash
# Run migration
cd /Users/sreekanthchityala/nettools/mytasks
source venv/bin/activate
python migrate_task_fields.py
```

### CSS Not Loading
1. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
2. Clear browser cache
3. Check browser console for errors

## 📊 Task Workflow

### Typical Daily Use
1. **Morning**: Check tasks, review deadlines
2. **Create Tasks**: Import from GitHub or create manually
3. **Update Status**: Use dropdown to track progress
4. **Set Reminders**: Add custom reminders for meetings
5. **Quick Links**: Access tools via sidebar
6. **Mute**: Silence reminders for tasks you're actively working on

### Best Practices
- Set realistic deadlines
- Use priority levels effectively
- Link GitHub issues for tracking
- Mute tasks only when actively working on them
- Review and archive completed tasks regularly

## 🎯 Tips & Tricks

1. **GitHub Integration**: Always link tasks to GitHub issues for better tracking
2. **Priority System**: Use Urgent sparingly for truly critical items
3. **Deadline vs Due Date**: Deadline triggers reminders, Due Date is informational
4. **Mute Wisely**: Mute when you're actively working, unmute when done
5. **Quick Access**: Customize sidebar links for your workflow
6. **Environments**: Use for different deployment stages
7. **Search**: Use link search to quickly find resources

## 📈 Future Enhancements (Phase 2)

Planned features:
- Edit task functionality
- Per-task custom reminder intervals (15min, 30min, 1hr, 3hr)
- Daily reminder option per task
- Multiple reminders per task
- Task templates
- Bulk operations
- Export/import tasks
- Team collaboration
- Mobile app

## 🆘 Support

For issues or questions:
1. Check this guide
2. Review error messages in browser console
3. Check database logs
4. Verify environment configuration

## 📝 Version History

**v1.0.0** - Initial Release
- GitHub integration
- Smart deadline reminders
- Task management
- Dashboard links
- Quick access sidebar
- Mute/unmute functionality
- Beautiful UI with animations

---

**Built with:** Flask, PostgreSQL, JavaScript, HTML/CSS
**Repository:** https://github.com/sreekanthops/mytasks
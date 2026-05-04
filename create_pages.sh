#!/bin/bash

# Create tasks.html
cat > templates/tasks.html << 'EOF'
{% extends "base.html" %}
{% block title %}My Tasks - Task Dashboard{% endblock %}
{% block page_title %}My Tasks{% endblock %}
{% block header_actions %}
<div class="header-actions">
    <select id="task-filter" class="form-control" onchange="loadTasks()">
        <option value="">All Tasks</option>
        <option value="pending">Pending</option>
        <option value="inprogress">In Progress</option>
        <option value="hold">On Hold</option>
        <option value="done">Done</option>
        <option value="archive">Archive</option>
    </select>
    <button class="btn btn-primary" onclick="openModal('task-modal')">
        <i class="fas fa-plus"></i> New Task
    </button>
</div>
{% endblock %}
{% block content %}
<div id="tasks-list"></div>
{% endblock %}
{% block modals %}
{% include 'modals/task_modal.html' %}
{% include 'modals/task_reminder_modal.html' %}
{% endblock %}
{% block scripts %}
<script src="{{ url_for('static', filename='js/tasks.js') }}"></script>
{% endblock %}
EOF

# Create reminders.html
cat > templates/reminders.html << 'EOF'
{% extends "base.html" %}
{% block title %}Reminders - Task Dashboard{% endblock %}
{% block page_title %}Reminders{% endblock %}
{% block header_actions %}
<button class="btn btn-primary" onclick="openModal('reminder-modal')">
    <i class="fas fa-plus"></i> New Reminder
</button>
{% endblock %}
{% block content %}
<div id="reminders-list"></div>
{% endblock %}
{% block modals %}
{% include 'modals/reminder_modal.html' %}
{% endblock %}
{% block scripts %}
<script src="{{ url_for('static', filename='js/reminders.js') }}"></script>
{% endblock %}
EOF

# Create links.html
cat > templates/links.html << 'EOF'
{% extends "base.html" %}
{% block title %}Dashboard Links - Task Dashboard{% endblock %}
{% block page_title %}Dashboard Links{% endblock %}
{% block header_actions %}
<div class="header-actions">
    <select id="env-filter" class="form-control" onchange="loadLinks()">
        <option value="">All Environments</option>
    </select>
    <button class="btn btn-secondary" onclick="showManageEnvModal()">
        <i class="fas fa-cog"></i> Manage Environments
    </button>
    <button class="btn btn-primary" onclick="openModal('link-modal')">
        <i class="fas fa-plus"></i> New Link
    </button>
</div>
{% endblock %}
{% block content %}
<div id="links-list"></div>
{% endblock %}
{% block modals %}
{% include 'modals/link_modal.html' %}
{% include 'modals/env_modal.html' %}
{% endblock %}
{% block scripts %}
<script src="{{ url_for('static', filename='js/links.js') }}"></script>
{% endblock %}
EOF

# Create settings.html
cat > templates/settings.html << 'EOF'
{% extends "base.html" %}
{% block title %}Settings - Task Dashboard{% endblock %}
{% block page_title %}Settings{% endblock %}
{% block content %}
<div class="card">
    <div class="card-header">
        <h3>GitHub Configuration</h3>
    </div>
    <div class="card-body">
        <form id="settings-form">
            <div class="form-group">
                <label for="github-token">GitHub Personal Access Token</label>
                <input type="password" id="github-token" class="form-control" placeholder="ghp_xxxxxxxxxxxx">
                <small class="form-text">Required to fetch GitHub issues</small>
            </div>
            <div class="form-group">
                <label for="github-username">GitHub Username</label>
                <input type="text" id="github-username" class="form-control" placeholder="your-username">
            </div>
            <button type="submit" class="btn btn-primary">Save Settings</button>
        </form>
    </div>
</div>
{% endblock %}
{% block scripts %}
<script src="{{ url_for('static', filename='js/settings.js') }}"></script>
{% endblock %}
EOF

echo "✅ Created all template files"

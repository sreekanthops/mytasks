#!/bin/bash

# Create tasks.js - placeholder that will load tasks
cat > tasks.js << 'EOF'
// Tasks page JavaScript
let currentTaskId = null;
let isEditMode = false;

// Load tasks on page load
document.addEventListener('DOMContentLoaded', function() {
    loadTasks();
    loadGithubIssuesForDropdown();
    
    // Setup task form submission
    const taskForm = document.getElementById('task-form');
    if (taskForm) {
        taskForm.addEventListener('submit', handleTaskSubmit);
    }
    
    // Setup GitHub issue dropdown change
    const githubIssueSelect = document.getElementById('task-github-issue');
    if (githubIssueSelect) {
        githubIssueSelect.addEventListener('change', handleGithubIssueSelect);
    }
});

// Load tasks from API
async function loadTasks() {
    const filter = document.getElementById('task-filter')?.value || '';
    try {
        const response = await fetch(`/api/tasks${filter ? '?status=' + filter : ''}`);
        const tasks = await response.json();
        displayTasks(tasks);
    } catch (error) {
        console.error('Error loading tasks:', error);
        showNotification('Failed to load tasks', 'error');
    }
}

// Display tasks
function displayTasks(tasks) {
    const tasksList = document.getElementById('tasks-list');
    if (!tasksList) return;
    
    if (tasks.length === 0) {
        tasksList.innerHTML = '<div class="empty-state"><p>No tasks found. Create your first task!</p></div>';
        return;
    }
    
    tasksList.innerHTML = tasks.map(task => createTaskCard(task)).join('');
}

// Create task card HTML
function createTaskCard(task) {
    const priorityColors = {
        low: '#10b981',
        medium: '#f59e0b',
        high: '#f97316',
        urgent: '#ef4444'
    };
    
    const statusIcons = {
        pending: '📋',
        inprogress: '⚡',
        hold: '⏸️',
        done: '✅',
        archive: '📦'
    };
    
    return `
        <div class="task-card" data-task-id="${task.id}">
            <div class="task-header">
                <h3>${task.title}</h3>
                <div class="task-actions">
                    <button class="btn-icon" onclick="muteTask(${task.id}, ${!task.is_muted})" title="${task.is_muted ? 'Unmute' : 'Mute'} reminders">
                        <i class="fas fa-bell${task.is_muted ? '-slash' : ''}"></i>
                    </button>
                    <button class="btn-icon" onclick="editTask(${task.id})" title="Edit task">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon" onclick="openReminderModal(${task.id}, '${task.title}')" title="Manage reminders">
                        <i class="fas fa-clock"></i>
                    </button>
                    <select class="status-select" onchange="updateTaskStatus(${task.id}, this.value)">
                        <option value="pending" ${task.status === 'pending' ? 'selected' : ''}>📋 Pending</option>
                        <option value="inprogress" ${task.status === 'inprogress' ? 'selected' : ''}>⚡ In Progress</option>
                        <option value="hold" ${task.status === 'hold' ? 'selected' : ''}>⏸️ On Hold</option>
                        <option value="done" ${task.status === 'done' ? 'selected' : ''}>✅ Done</option>
                        <option value="archive" ${task.status === 'archive' ? 'selected' : ''}>📦 Archive</option>
                    </select>
                    <button class="btn-icon btn-danger" onclick="deleteTask(${task.id})" title="Delete task">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            ${task.description ? `<p class="task-description">${task.description}</p>` : ''}
            <div class="task-meta">
                <span class="priority-badge" style="background: ${priorityColors[task.priority]}">
                    ${task.priority.toUpperCase()}
                </span>
                ${task.deadline ? `<span class="deadline">⏰ ${new Date(task.deadline).toLocaleString()}</span>` : ''}
            </div>
        </div>
    `;
}

// Handle task form submission
async function handleTaskSubmit(e) {
    e.preventDefault();
    
    const taskData = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-description').value,
        status: document.getElementById('task-status').value,
        priority: document.getElementById('task-priority').value,
        deadline: document.getElementById('task-deadline').value,
        due_date: document.getElementById('task-due-date').value
    };
    
    // Add GitHub issue data if selected
    const githubIssueSelect = document.getElementById('task-github-issue');
    if (githubIssueSelect && githubIssueSelect.value) {
        const selectedOption = githubIssueSelect.options[githubIssueSelect.selectedIndex];
        taskData.github_issue_number = parseInt(githubIssueSelect.value);
        taskData.github_issue_title = selectedOption.dataset.title;
        taskData.github_issue_url = selectedOption.dataset.url;
    }
    
    try {
        const url = isEditMode ? `/api/tasks/${currentTaskId}` : '/api/tasks';
        const method = isEditMode ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        
        if (response.ok) {
            showNotification(isEditMode ? 'Task updated successfully' : 'Task created successfully', 'success');
            closeModal('task-modal');
            loadTasks();
            resetTaskForm();
        } else {
            throw new Error('Failed to save task');
        }
    } catch (error) {
        console.error('Error saving task:', error);
        showNotification('Failed to save task', 'error');
    }
}

// Edit task
async function editTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}`);
        const task = await response.json();
        
        // Fill form with task data
        document.getElementById('task-title').value = task.title;
        document.getElementById('task-description').value = task.description || '';
        document.getElementById('task-status').value = task.status;
        document.getElementById('task-priority').value = task.priority;
        document.getElementById('task-deadline').value = task.deadline ? task.deadline.slice(0, 16) : '';
        document.getElementById('task-due-date').value = task.due_date ? task.due_date.slice(0, 16) : '';
        
        // Set GitHub issue if exists
        if (task.github_issue_number) {
            const githubSelect = document.getElementById('task-github-issue');
            if (githubSelect) {
                githubSelect.value = task.github_issue_number;
            }
        }
        
        // Update form mode
        isEditMode = true;
        currentTaskId = taskId;
        
        // Update button text
        const submitBtn = document.querySelector('#task-form button[type="submit"]');
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fas fa-save"></i> Update Task';
        }
        
        // Update modal title
        const modalTitle = document.querySelector('#task-modal .modal-header h3');
        if (modalTitle) {
            modalTitle.textContent = 'Edit Task';
        }
        
        openModal('task-modal');
    } catch (error) {
        console.error('Error loading task:', error);
        showNotification('Failed to load task', 'error');
    }
}

// Reset task form
function resetTaskForm() {
    isEditMode = false;
    currentTaskId = null;
    document.getElementById('task-form').reset();
    
    const submitBtn = document.querySelector('#task-form button[type="submit"]');
    if (submitBtn) {
        submitBtn.innerHTML = '<i class="fas fa-plus"></i> Add Task';
    }
    
    const modalTitle = document.querySelector('#task-modal .modal-header h3');
    if (modalTitle) {
        modalTitle.textContent = 'Add New Task';
    }
}

// Update task status
async function updateTaskStatus(taskId, status) {
    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        
        if (response.ok) {
            showNotification('Task status updated', 'success');
            loadTasks();
        }
    } catch (error) {
        console.error('Error updating task:', error);
        showNotification('Failed to update task', 'error');
    }
}

// Delete task
async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    try {
        const response = await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Task deleted successfully', 'success');
            loadTasks();
        }
    } catch (error) {
        console.error('Error deleting task:', error);
        showNotification('Failed to delete task', 'error');
    }
}

// Mute/unmute task
async function muteTask(taskId, mute) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/mute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mute })
        });
        
        if (response.ok) {
            showNotification(mute ? 'Task muted' : 'Task unmuted', 'success');
            loadTasks();
        }
    } catch (error) {
        console.error('Error muting task:', error);
        showNotification('Failed to update task', 'error');
    }
}

// Load GitHub issues for dropdown
async function loadGithubIssuesForDropdown() {
    try {
        const response = await fetch('/api/github/issues?status=open');
        const issues = await response.json();
        
        const select = document.getElementById('task-github-issue');
        if (!select) return;
        
        select.innerHTML = '<option value="">-- No GitHub Issue --</option>';
        issues.forEach(issue => {
            const option = document.createElement('option');
            option.value = issue.number;
            option.textContent = `#${issue.number} - ${issue.title}`;
            option.dataset.title = issue.title;
            option.dataset.url = issue.html_url;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading GitHub issues:', error);
    }
}

// Handle GitHub issue selection
function handleGithubIssueSelect(e) {
    const selectedOption = e.target.options[e.target.selectedIndex];
    if (selectedOption.value) {
        document.getElementById('task-title').value = selectedOption.dataset.title;
    }
}

// Open reminder modal for task
function openReminderModal(taskId, taskTitle) {
    currentTaskId = taskId;
    document.getElementById('reminder-task-title').textContent = taskTitle;
    openModal('task-reminder-modal');
    loadTaskReminders(taskId);
}

// Close reminder modal
function closeReminderModal() {
    closeModal('task-reminder-modal');
    currentTaskId = null;
}

// Load task reminders
async function loadTaskReminders(taskId) {
    try {
        const response = await fetch(`/api/task-reminders/${taskId}`);
        const reminders = await response.json();
        displayTaskReminders(reminders);
    } catch (error) {
        console.error('Error loading reminders:', error);
    }
}

// Display task reminders
function displayTaskReminders(reminders) {
    const list = document.getElementById('task-reminders-list');
    if (!list) return;
    
    if (reminders.length === 0) {
        list.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">No reminders set for this task</p>';
        return;
    }
    
    list.innerHTML = reminders.map(r => `
        <div class="reminder-item" style="padding: 12px; background: var(--hover-bg); border-radius: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>${r.reminder_type === 'before_deadline' ? `${r.interval_minutes} min before deadline` : 
                         r.reminder_type === 'daily' ? `Daily at ${r.custom_time}` : 
                         `Custom: ${new Date(r.custom_time).toLocaleString()}`}</strong>
                <span style="display: block; font-size: 12px; color: var(--text-secondary);">
                    ${r.is_active ? '✅ Active' : '⏸️ Inactive'}
                </span>
            </div>
            <button class="btn btn-danger btn-sm" onclick="deleteTaskReminder(${r.id})">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `).join('');
}

// Add quick reminder
async function addQuickReminder(minutes) {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch('/api/task-reminders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                task_id: currentTaskId,
                reminder_type: 'before_deadline',
                interval_minutes: minutes
            })
        });
        
        if (response.ok) {
            showNotification('Reminder added', 'success');
            loadTaskReminders(currentTaskId);
        }
    } catch (error) {
        console.error('Error adding reminder:', error);
        showNotification('Failed to add reminder', 'error');
    }
}

// Add daily reminder
async function addDailyReminder() {
    if (!currentTaskId) return;
    
    const time = document.getElementById('daily-reminder-time').value;
    if (!time) {
        showNotification('Please select a time', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/task-reminders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                task_id: currentTaskId,
                reminder_type: 'daily',
                custom_time: time
            })
        });
        
        if (response.ok) {
            showNotification('Daily reminder added', 'success');
            document.getElementById('daily-reminder-time').value = '';
            loadTaskReminders(currentTaskId);
        }
    } catch (error) {
        console.error('Error adding reminder:', error);
        showNotification('Failed to add reminder', 'error');
    }
}

// Add custom reminder
async function addCustomReminder() {
    if (!currentTaskId) return;
    
    const datetime = document.getElementById('custom-reminder-datetime').value;
    if (!datetime) {
        showNotification('Please select a date and time', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/task-reminders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                task_id: currentTaskId,
                reminder_type: 'custom',
                custom_time: datetime
            })
        });
        
        if (response.ok) {
            showNotification('Custom reminder added', 'success');
            document.getElementById('custom-reminder-datetime').value = '';
            loadTaskReminders(currentTaskId);
        }
    } catch (error) {
        console.error('Error adding reminder:', error);
        showNotification('Failed to add reminder', 'error');
    }
}

// Delete task reminder
async function deleteTaskReminder(reminderId) {
    if (!confirm('Delete this reminder?')) return;
    
    try {
        const response = await fetch(`/api/task-reminders/${reminderId}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Reminder deleted', 'success');
            loadTaskReminders(currentTaskId);
        }
    } catch (error) {
        console.error('Error deleting reminder:', error);
        showNotification('Failed to delete reminder', 'error');
    }
}
EOF

# Create reminders.js - placeholder
cat > reminders.js << 'EOF'
// Reminders page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    loadReminders();
    
    const reminderForm = document.getElementById('reminder-form');
    if (reminderForm) {
        reminderForm.addEventListener('submit', handleReminderSubmit);
    }
});

async function loadReminders() {
    try {
        const response = await fetch('/api/reminders');
        const reminders = await response.json();
        displayReminders(reminders);
    } catch (error) {
        console.error('Error loading reminders:', error);
    }
}

function displayReminders(reminders) {
    const list = document.getElementById('reminders-list');
    if (!list) return;
    
    if (reminders.length === 0) {
        list.innerHTML = '<div class="empty-state"><p>No reminders set</p></div>';
        return;
    }
    
    list.innerHTML = reminders.map(r => `
        <div class="reminder-card">
            <h3>${r.title}</h3>
            ${r.description ? `<p>${r.description}</p>` : ''}
            <div class="reminder-time">⏰ ${new Date(r.reminder_time).toLocaleString()}</div>
            <button class="btn btn-danger btn-sm" onclick="deleteReminder(${r.id})">Delete</button>
        </div>
    `).join('');
}

async function handleReminderSubmit(e) {
    e.preventDefault();
    
    const data = {
        title: document.getElementById('reminder-title').value,
        description: document.getElementById('reminder-description').value,
        reminder_time: document.getElementById('reminder-time').value
    };
    
    try {
        const response = await fetch('/api/reminders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showNotification('Reminder created', 'success');
            closeModal('reminder-modal');
            loadReminders();
            e.target.reset();
        }
    } catch (error) {
        console.error('Error creating reminder:', error);
        showNotification('Failed to create reminder', 'error');
    }
}

async function deleteReminder(id) {
    if (!confirm('Delete this reminder?')) return;
    
    try {
        const response = await fetch(`/api/reminders/${id}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Reminder deleted', 'success');
            loadReminders();
        }
    } catch (error) {
        console.error('Error deleting reminder:', error);
    }
}
EOF

# Create links.js - placeholder
cat > links.js << 'EOF'
// Links page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    loadLinks();
    loadEnvironments();
    
    const linkForm = document.getElementById('link-form');
    if (linkForm) {
        linkForm.addEventListener('submit', handleLinkSubmit);
    }
    
    const envForm = document.getElementById('env-form');
    if (envForm) {
        envForm.addEventListener('submit', handleEnvSubmit);
    }
});

async function loadLinks() {
    const envFilter = document.getElementById('env-filter')?.value || '';
    try {
        const response = await fetch(`/api/links${envFilter ? '?environment_id=' + envFilter : ''}`);
        const links = await response.json();
        displayLinks(links);
    } catch (error) {
        console.error('Error loading links:', error);
    }
}

function displayLinks(links) {
    const list = document.getElementById('links-list');
    if (!list) return;
    
    if (links.length === 0) {
        list.innerHTML = '<div class="empty-state"><p>No links found</p></div>';
        return;
    }
    
    list.innerHTML = links.map(link => `
        <div class="link-card">
            <h3><a href="${link.url}" target="_blank">${link.name}</a></h3>
            ${link.description ? `<p>${link.description}</p>` : ''}
            ${link.environment ? `<span class="env-badge">${link.environment.name}</span>` : ''}
            <button class="btn btn-danger btn-sm" onclick="deleteLink(${link.id})">Delete</button>
        </div>
    `).join('');
}

async function loadEnvironments() {
    try {
        const response = await fetch('/api/environments');
        const envs = await response.json();
        
        // Update filter dropdown
        const filter = document.getElementById('env-filter');
        if (filter) {
            filter.innerHTML = '<option value="">All Environments</option>' +
                envs.map(e => `<option value="${e.id}">${e.name}</option>`).join('');
        }
        
        // Update link form dropdown
        const linkEnv = document.getElementById('link-environment');
        if (linkEnv) {
            linkEnv.innerHTML = '<option value="">No Environment</option>' +
                envs.map(e => `<option value="${e.id}">${e.name}</option>`).join('');
        }
        
        // Display in env modal
        const envList = document.getElementById('env-list');
        if (envList) {
            envList.innerHTML = envs.map(e => `
                <div class="env-item" style="padding: 10px; background: var(--hover-bg); border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 20px; height: 20px; border-radius: 4px; background: ${e.color};"></div>
                        <span>${e.name}</span>
                    </div>
                    <button class="btn btn-danger btn-sm" onclick="deleteEnvironment(${e.id})">Delete</button>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading environments:', error);
    }
}

async function handleLinkSubmit(e) {
    e.preventDefault();
    
    const data = {
        name: document.getElementById('link-name').value,
        url: document.getElementById('link-url').value,
        description: document.getElementById('link-description').value,
        environment_id: document.getElementById('link-environment').value || null
    };
    
    try {
        const response = await fetch('/api/links', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showNotification('Link created', 'success');
            closeModal('link-modal');
            loadLinks();
            e.target.reset();
        }
    } catch (error) {
        console.error('Error creating link:', error);
        showNotification('Failed to create link', 'error');
    }
}

async function handleEnvSubmit(e) {
    e.preventDefault();
    
    const data = {
        name: document.getElementById('env-name').value,
        color: document.getElementById('env-color').value
    };
    
    try {
        const response = await fetch('/api/environments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showNotification('Environment created', 'success');
            loadEnvironments();
            e.target.reset();
        }
    } catch (error) {
        console.error('Error creating environment:', error);
        showNotification('Failed to create environment', 'error');
    }
}

async function deleteLink(id) {
    if (!confirm('Delete this link?')) return;
    
    try {
        const response = await fetch(`/api/links/${id}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Link deleted', 'success');
            loadLinks();
        }
    } catch (error) {
        console.error('Error deleting link:', error);
    }
}

async function deleteEnvironment(id) {
    if (!confirm('Delete this environment?')) return;
    
    try {
        const response = await fetch(`/api/environments/${id}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Environment deleted', 'success');
            loadEnvironments();
            loadLinks();
        }
    } catch (error) {
        console.error('Error deleting environment:', error);
    }
}

function showManageEnvModal() {
    openModal('env-modal');
}
EOF

# Create settings.js - simple placeholder
cat > settings.js << 'EOF'
// Settings page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    loadSettings();
    
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', handleSettingsSubmit);
    }
});

async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const settings = await response.json();
        
        if (settings.github_token) {
            document.getElementById('github-token').value = settings.github_token;
        }
        if (settings.github_username) {
            document.getElementById('github-username').value = settings.github_username;
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

async function handleSettingsSubmit(e) {
    e.preventDefault();
    
    const data = {
        github_token: document.getElementById('github-token').value,
        github_username: document.getElementById('github-username').value
    };
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showNotification('Settings saved successfully', 'success');
        } else {
            throw new Error('Failed to save settings');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showNotification('Failed to save settings', 'error');
    }
}
EOF

echo "✅ Created all JavaScript files"

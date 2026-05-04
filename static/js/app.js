// Global state
let currentSection = 'github';
let reminderCheckInterval = null;
let githubIssuesCache = [];

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    updateTime();
    setInterval(updateTime, 1000);
    loadSettings();
    loadGithubIssues();
    setupFormHandlers();
    requestNotificationPermission();
    startReminderChecker();
    loadEnvironments();
});

// Request notification permission
async function requestNotificationPermission() {
    if ('Notification' in window) {
        if (Notification.permission === 'default') {
            await Notification.requestPermission();
        }
    }
}

// Start checking reminders
function startReminderChecker() {
    checkReminders();
    checkDeadlineReminders();
    checkTaskReminders();
    reminderCheckInterval = setInterval(() => {
        checkReminders();
        checkDeadlineReminders();
        checkTaskReminders();
    }, 30000);
}

// Check reminders
async function checkReminders() {
    try {
        const response = await fetch('/api/reminders');
        const reminders = await response.json();
        const now = new Date();
        reminders.forEach(reminder => {
            const reminderTime = new Date(reminder.reminder_time);
            const timeDiff = reminderTime - now;
            if (timeDiff <= 60000 && timeDiff >= -60000) {
                showReminderNotification(reminder);
            }
        });
    } catch (error) {
        console.error('Error checking reminders:', error);
    }
}

// Check deadline reminders
async function checkDeadlineReminders() {
    try {
        const response = await fetch('/api/deadline-reminders');
        const deadlineReminders = await response.json();
        deadlineReminders.forEach(reminder => {
            showDeadlineNotification(reminder);
        });
    } catch (error) {
        console.error('Error checking deadline reminders:', error);
    }
}

// Check task reminders
async function checkTaskReminders() {
    try {
        const response = await fetch('/api/task-reminders/check');
        const taskReminders = await response.json();
        taskReminders.forEach(reminder => {
            playNotificationSound();
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification(reminder.message, {
                    body: `Priority: ${reminder.priority}`,
                    icon: '/static/favicon.ico'
                });
            }
            showToast(reminder.message, reminder.priority === 'urgent' ? 'critical' : 'warning');
        });
    } catch (error) {
        console.error('Error checking task reminders:', error);
    }
}

function showDeadlineNotification(reminder) {
    playNotificationSound();
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(reminder.message, {
            body: `Deadline: ${new Date(reminder.deadline).toLocaleString()}`,
            icon: '/static/favicon.ico'
        });
    }
    showToast(reminder.message, reminder.urgency);
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 20px;">${type === 'overdue' ? '⚠️' : type === 'critical' ? '🔴' : '🟡'}</span>
        <div style="flex: 1;"><strong>${message}</strong></div>
        <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; font-size: 20px; cursor: pointer; color: inherit;">×</button>
    </div>`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), type === 'overdue' || type === 'critical' ? 30000 : 10000);
}

async function muteTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/mute`, { method: 'POST' });
        if (response.ok) {
            const result = await response.json();
            showNotification(result.message, 'success');
            loadTasks();
        }
    } catch (error) {
        showNotification('Error muting task', 'error');
    }
}

function showReminderNotification(reminder) {
    playNotificationSound();
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Reminder: ' + reminder.title, {
            body: reminder.description || 'Time for your reminder!',
            icon: '/static/favicon.ico'
        });
    }
}

function playNotificationSound() {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    oscillator.frequency.value = 800;
    oscillator.type = 'sine';
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
}

function initializeNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            switchSection(this.dataset.section);
        });
    });
}

function switchSection(section) {
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    document.querySelector(`[data-section="${section}"]`).classList.add('active');
    document.querySelectorAll('.content-section').forEach(sec => sec.classList.remove('active'));
    document.getElementById(`${section}-section`).classList.add('active');
    const titles = { 'github': 'GitHub Issues', 'tasks': 'My Tasks', 'reminders': 'Reminders', 'links': 'Dashboard Links', 'settings': 'Settings' };
    document.getElementById('section-title').textContent = titles[section];
    currentSection = section;
    switch(section) {
        case 'github': loadGithubIssues(); break;
        case 'tasks': loadTasks(); break;
        case 'reminders': loadReminders(); break;
        case 'links': loadLinks(); break;
        case 'settings': loadSettings(); break;
    }
}

function updateTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleDateString('en-US', { 
        weekday: 'short', year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
}

async function loadGithubIssues() {
    const container = document.getElementById('github-issues');
    const status = document.getElementById('github-status').value;
    container.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i> Loading issues...</div>';
    try {
        const response = await fetch(`/api/github/issues?status=${status}`);
        const data = await response.json();
        if (response.ok) {
            githubIssuesCache = data;
            if (data.length === 0) {
                container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📋</div><h3>No ${status} issues found</h3><p>All caught up!</p></div>`;
            } else {
                container.innerHTML = data.map(issue => `
                    <div class="card">
                        <div class="card-header">
                            <div>
                                <div class="card-title">#${issue.number} - ${issue.title}</div>
                                <div class="flex gap-2" style="margin-top: 8px;">
                                    <span class="badge badge-${issue.state}">${issue.state}</span>
                                    ${issue.labels.map(label => `<span class="badge" style="background: #${label.color}20; color: #${label.color};">${label.name}</span>`).join('')}
                                </div>
                            </div>
                        </div>
                        ${issue.body ? `<div class="card-body">${issue.body.substring(0, 200)}${issue.body.length > 200 ? '...' : ''}</div>` : ''}
                        <div class="card-footer">
                            <span class="card-time">Updated: ${new Date(issue.updated_at).toLocaleDateString()}</span>
                            <a href="${issue.html_url}" target="_blank" class="btn btn-primary"><i class="fab fa-github"></i> View on GitHub</a>
                        </div>
                    </div>
                `).join('');
            }
        } else {
            container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><h3>Error loading issues</h3><p>${data.error || 'Please check your GitHub token in settings'}</p></div>`;
        }
    } catch (error) {
        container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><h3>Error loading issues</h3><p>${error.message}</p></div>`;
    }
}

async function loadTasks() {
    const container = document.getElementById('tasks-list');
    const filter = document.getElementById('task-filter').value;
    container.innerHTML = '<div class="spinner"></div>';
    try {
        const url = filter ? `/api/tasks?status=${filter}` : '/api/tasks';
        const response = await fetch(url);
        const tasks = await response.json();
        if (tasks.length === 0) {
            container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📋</div><h3>No tasks found</h3><p>Create your first task to get started!</p></div>`;
        } else {
            const priorityColors = { low: '#10b981', medium: '#f59e0b', high: '#f97316', urgent: '#ef4444' };
            const priorityIcons = { low: '🟢', medium: '🟡', high: '🟠', urgent: '🔴' };
            container.innerHTML = tasks.map(task => `
                <div class="card task-card">
                    <div class="card-header">
                        <div style="flex: 1;">
                            ${task.github_issue_number ? `
                                <div style="margin-bottom: 8px;">
                                    <a href="${task.github_issue_url}" target="_blank" class="github-ticket-badge" style="display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-decoration: none; box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);">
                                        <i class="fab fa-github"></i> #${task.github_issue_number}
                                    </a>
                                </div>
                            ` : ''}
                            <div class="card-title">${task.title}</div>
                            <div class="flex gap-2" style="margin-top: 8px; flex-wrap: wrap;">
                                <span class="badge badge-${task.status}">${task.status.replace('inprogress', 'in progress')}</span>
                                ${task.priority ? `<span class="badge" style="background: ${priorityColors[task.priority]}20; color: ${priorityColors[task.priority]};">${priorityIcons[task.priority]} ${task.priority}</span>` : ''}
                                ${task.deadline ? `<span class="badge" style="background: rgba(239, 68, 68, 0.1); color: #ef4444;"><i class="fas fa-clock"></i> ${new Date(task.deadline).toLocaleDateString()}</span>` : ''}
                                ${task.due_date ? `<span class="badge" style="background: rgba(99, 102, 241, 0.1); color: #6366f1;"><i class="fas fa-calendar"></i> ${new Date(task.due_date).toLocaleDateString()}</span>` : ''}
                                ${task.reminder_count > 0 ? `<span class="badge" style="background: rgba(139, 92, 246, 0.1); color: #8b5cf6;"><i class="fas fa-bell"></i> ${task.reminder_count} reminder${task.reminder_count > 1 ? 's' : ''}</span>` : ''}
                            </div>
                        </div>
                    </div>
                    ${task.description ? `<div class="card-body" style="margin-top: 12px; color: var(--text-secondary); font-size: 14px;">${task.description}</div>` : ''}
                    <div class="card-footer">
                        <span style="font-size: 12px; color: var(--text-secondary);">
                            <i class="fas fa-clock"></i> ${new Date(task.created_at).toLocaleDateString()}
                            ${task.is_muted ? '<span class="badge" style="background: rgba(100, 116, 139, 0.2); color: #64748b; margin-left: 8px;"><i class="fas fa-bell-slash"></i> Muted</span>' : ''}
                        </span>
                        <div class="flex gap-2">
                            <button class="btn btn-sm ${task.is_muted ? 'btn-secondary' : 'btn-warning'}" onclick="muteTask(${task.id})" title="${task.deadline ? (task.is_muted ? '🔔 Unmute deadline alerts' : '🔕 Mute deadline alerts') : '⚠️ Add a deadline to enable alerts'}" ${!task.deadline ? 'disabled style="opacity: 0.5; cursor: not-allowed;"' : ''}>
                                <i class="fas fa-bell${task.is_muted ? '' : '-slash'}"></i>
                            </button>
                            <button class="btn btn-sm btn-primary" onclick="editTask(${task.id})" title="✏️ Edit task">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm" style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; border: none;" onclick="openReminderModal(${task.id}, '${task.title.replace(/'/g, "\\'")}', ${task.deadline ? `'${task.deadline}'` : 'null'})" title="⏰ Manage custom reminders">
                                <i class="fas fa-clock"></i>
                            </button>
                            <select class="form-control" onchange="updateTaskStatus(${task.id}, this.value)" style="padding: 8px 12px; font-size: 13px; width: auto;">
                                <option value="pending" ${task.status === 'pending' ? 'selected' : ''}>📋 Pending</option>
                                <option value="inprogress" ${task.status === 'inprogress' ? 'selected' : ''}>⚡ In Progress</option>
                                <option value="hold" ${task.status === 'hold' ? 'selected' : ''}>⏸️ On Hold</option>
                                <option value="done" ${task.status === 'done' ? 'selected' : ''}>✅ Done</option>
                                <option value="archive" ${task.status === 'archive' ? 'selected' : ''}>📦 Archive</option>
                            </select>
                            <button class="btn btn-danger btn-sm" onclick="deleteTask(${task.id})"><i class="fas fa-trash"></i></button>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><h3>Error loading tasks</h3><p>${error.message}</p></div>`;
    }
}

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
        showNotification('Error updating task', 'error');
    }
}

async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    try {
        const response = await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Task deleted successfully', 'success');
            loadTasks();
        }
    } catch (error) {
        showNotification('Error deleting task', 'error');
    }
}

async function editTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}`);
        if (!response.ok) {
            showNotification('Error loading task', 'error');
            return;
        }
        const task = await response.json();
        
        // Populate the task form with existing data
        document.getElementById('task-title').value = task.title;
        document.getElementById('task-description').value = task.description || '';
        document.getElementById('task-status').value = task.status;
        document.getElementById('task-priority').value = task.priority || 'medium';
        document.getElementById('task-deadline').value = task.deadline ? task.deadline.split('T')[0] : '';
        document.getElementById('task-due-date').value = task.due_date ? task.due_date.split('T')[0] : '';
        
        // If task has GitHub issue, show it (read-only in edit mode)
        if (task.github_issue_number) {
            const githubSelect = document.getElementById('task-github-issue');
            githubSelect.innerHTML = `<option value="" selected>#${task.github_issue_number} - ${task.github_issue_title} (linked)</option>`;
            githubSelect.disabled = true;
        }
        
        // Change modal title
        document.querySelector('#task-modal .modal-header h2').textContent = 'Edit Task';
        
        // Change form submit handler to update instead of create
        const form = document.getElementById('task-form');
        const originalHandler = form.onsubmit;
        
        form.onsubmit = async function(e) {
            e.preventDefault();
            const updateData = {
                title: document.getElementById('task-title').value,
                description: document.getElementById('task-description').value,
                status: document.getElementById('task-status').value,
                priority: document.getElementById('task-priority').value,
                deadline: document.getElementById('task-deadline').value || null,
                due_date: document.getElementById('task-due-date').value || null
            };
            
            try {
                const updateResponse = await fetch(`/api/tasks/${taskId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updateData)
                });
                
                if (updateResponse.ok) {
                    showNotification('Task updated successfully!', 'success');
                    closeModal('task-modal');
                    form.reset();
                    // Reset form back to create mode
                    document.querySelector('#task-modal .modal-header h2').textContent = 'Create New Task';
                    const githubSelect = document.getElementById('task-github-issue');
                    githubSelect.disabled = false;
                    setupFormHandlers();
                    loadTasks();
                }
            } catch (error) {
                showNotification('Error updating task', 'error');
            }
        };
        
        openModal('task-modal');
    } catch (error) {
        showNotification('Error loading task', 'error');
    }
}

async function loadReminders() {
    const container = document.getElementById('reminders-list');
    container.innerHTML = '<div class="spinner"></div>';
    try {
        const response = await fetch('/api/reminders');
        const reminders = await response.json();
        if (reminders.length === 0) {
            container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🔔</div><h3>No reminders set</h3><p>Create a reminder to stay on track!</p></div>`;
        } else {
            container.innerHTML = reminders.map(reminder => `
                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">${reminder.title}</div>
                            <div class="card-time"><i class="fas fa-clock"></i> ${new Date(reminder.reminder_time).toLocaleString()}</div>
                        </div>
                    </div>
                    ${reminder.description ? `<div class="card-body">${reminder.description}</div>` : ''}
                    <div class="card-footer">
                        <span class="card-time">Created: ${new Date(reminder.created_at).toLocaleDateString()}</span>
                        <button class="btn btn-danger" onclick="deleteReminder(${reminder.id})"><i class="fas fa-trash"></i> Delete</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><h3>Error loading reminders</h3><p>${error.message}</p></div>`;
    }
}

async function deleteReminder(reminderId) {
    if (!confirm('Are you sure you want to delete this reminder?')) return;
    try {
        const response = await fetch(`/api/reminders/${reminderId}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Reminder deleted successfully', 'success');
            loadReminders();
        }
    } catch (error) {
        showNotification('Error deleting reminder', 'error');
    }
}

async function loadLinks() {
    const container = document.getElementById('links-list');
    const envFilter = document.getElementById('env-filter').value;
    container.innerHTML = '<div class="spinner"></div>';
    try {
        const url = envFilter ? `/api/links?environment_id=${envFilter}` : '/api/links';
        const response = await fetch(url);
        const links = await response.json();
        if (links.length === 0) {
            container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🔗</div><h3>No links found</h3><p>Add your first dashboard link!</p></div>`;
        } else {
            container.innerHTML = links.map(link => `
                <div class="card link-card" onclick="window.open('${link.url}', '_blank')" style="cursor: pointer;">
                    <div class="card-header">
                        <div>
                            <div class="card-title">${link.name}</div>
                            ${link.environment ? `<span class="badge" style="background: ${link.environment_color}20; color: ${link.environment_color}; margin-top: 5px;">${link.environment}</span>` : ''}
                            <div class="link-url">${link.url}</div>
                        </div>
                    </div>
                    ${link.description ? `<div class="card-description">${link.description}</div>` : ''}
                    <div class="card-footer">
                        <span class="card-time">Added: ${new Date(link.created_at).toLocaleDateString()}</span>
                        <button class="btn btn-danger" onclick="event.stopPropagation(); deleteLink(${link.id})"><i class="fas fa-trash"></i></button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        container.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Error loading links: ${error.message}</p></div>`;
    }
}

async function deleteLink(linkId) {
    if (!confirm('Are you sure you want to delete this link?')) return;
    try {
        const response = await fetch(`/api/links/${linkId}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Link deleted successfully', 'success');
            loadLinks();
        }
    } catch (error) {
        showNotification('Error deleting link', 'error');
    }
}

async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const settings = await response.json();
        document.getElementById('github-token').value = settings.github_token || '';
        document.getElementById('github-username').value = settings.github_username || '';
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

function setupFormHandlers() {
    document.getElementById('task-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const githubIssue = document.getElementById('task-github-issue').value;
        const data = {
            title: document.getElementById('task-title').value,
            description: document.getElementById('task-description').value,
            status: document.getElementById('task-status').value,
            due_date: document.getElementById('task-due-date').value || null,
            priority: document.getElementById('task-priority').value,
            deadline: document.getElementById('task-deadline').value || null
        };
        if (githubIssue) {
            const issueNum = githubIssue.split(' - ')[0].replace('#', '');
            const issue = githubIssuesCache.find(i => i.number == issueNum);
            if (issue) {
                data.github_issue_number = issue.number;
                data.github_issue_title = issue.title;
                data.github_issue_url = issue.html_url;
            }
        }
        try {
            const response = await fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (response.ok) {
                showNotification('Task created successfully!', 'success');
                closeModal('task-modal');
                this.reset();
                switchSection('tasks');
            }
        } catch (error) {
            showNotification('Error creating task', 'error');
        }
    });
    
    document.getElementById('reminder-form').addEventListener('submit', async function(e) {
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
                showNotification('Reminder created successfully!', 'success');
                closeModal('reminder-modal');
                this.reset();
                switchSection('reminders');
            }
        } catch (error) {
            showNotification('Error creating reminder', 'error');
        }
    });
    
    document.getElementById('link-form').addEventListener('submit', async function(e) {
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
                showNotification('Link added successfully!', 'success');
                closeModal('link-modal');
                this.reset();
                switchSection('links');
            }
        } catch (error) {
            showNotification('Error adding link', 'error');
        }
    });
    
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', async function(e) {
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
                showNotification('Settings saved successfully!', 'success');
            }
        } catch (error) {
            showNotification('Error saving settings', 'error');
        }
        });
    }
    
    const envForm = document.getElementById('env-form');
    if (envForm) {
        envForm.addEventListener('submit', async function(e) {
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
                showNotification('Environment created!', 'success');
                this.reset();
                loadEnvironmentsList();
            }
        } catch (error) {
            showNotification('Error creating environment', 'error');
        }
        });
    }
}

function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
    if (modalId === 'task-modal') {
        loadGithubIssuesForTask();
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.classList.add('show'), 10);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

async function loadGithubIssuesForTask() {
    const select = document.getElementById('task-github-issue');
    select.innerHTML = '<option value="">Loading open issues...</option>';
    try {
        const response = await fetch('/api/github/issues?status=open');
        const issues = await response.json();
        if (response.ok && issues.length > 0) {
            githubIssuesCache = issues;
            select.innerHTML = '<option value="">Select a GitHub issue (optional)</option>' +
                issues.map(issue => `<option value="#${issue.number} - ${issue.title}">#${issue.number} - ${issue.title}</option>`).join('');
        } else {
            select.innerHTML = '<option value="">No open issues found</option>';
        }
    } catch (error) {
        select.innerHTML = '<option value="">Error loading issues</option>';
    }
}

async function showImportGithubModal() {
    const modal = document.getElementById('github-import-modal');
    const select = document.getElementById('github-issue-select');
    modal.classList.add('active');
    select.innerHTML = '<option value="">Loading open issues...</option>';
    try {
        const response = await fetch('/api/github/issues?status=open');
        const issues = await response.json();
        if (response.ok && issues.length > 0) {
            githubIssuesCache = issues;
            select.innerHTML = issues.map(issue => `<option value="${issue.number}">#${issue.number} - ${issue.title}</option>`).join('');
        } else {
            select.innerHTML = '<option value="">No open issues found</option>';
        }
    } catch (error) {
        select.innerHTML = '<option value="">Error loading issues</option>';
    }
}

async function importSelectedIssue() {
    const select = document.getElementById('github-issue-select');
    const issueNumber = select.value;
    if (!issueNumber) {
        showNotification('Please select an issue to import', 'warning');
        return;
    }
    try {
        const response = await fetch(`/api/tasks/from-github/${issueNumber}`, { method: 'POST' });
        if (response.ok) {
            showNotification('GitHub issue imported as task!', 'success');
            closeModal('github-import-modal');
            switchSection('tasks');
        }
    } catch (error) {
        showNotification('Error importing issue', 'error');
    }
}

async function showManageEnvModal() {
    document.getElementById('env-modal').classList.add('active');
    loadEnvironmentsList();
}

async function loadEnvironmentsList() {
    const container = document.getElementById('env-list');
    try {
        const response = await fetch('/api/environments');
        const environments = await response.json();
        if (environments.length === 0) {
            container.innerHTML = '<p style="color: #64748b; text-align: center; padding: 20px;">No environments created yet</p>';
        } else {
            container.innerHTML = environments.map(env => `
                <div class="env-item" style="display: flex; align-items: center; justify-content: space-between; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 10px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 20px; height: 20px; border-radius: 4px; background: ${env.color};"></div>
                        <strong>${env.name}</strong>
                        <span style="color: #64748b; font-size: 12px;">(${env.link_count} links)</span>
                    </div>
                    <button class="btn btn-danger" onclick="deleteEnvironment(${env.id})"><i class="fas fa-trash"></i></button>
                </div>
            `).join('');
        }
        updateEnvironmentDropdowns(environments);
    } catch (error) {
        container.innerHTML = '<p style="color: #ef4444;">Error loading environments</p>';
    }
}

function updateEnvironmentDropdowns(environments) {
    const linkEnvSelect = document.getElementById('link-environment');
    const envFilter = document.getElementById('env-filter');
    linkEnvSelect.innerHTML = '<option value="">No Environment</option>' +
        environments.map(env => `<option value="${env.id}">${env.name}</option>`).join('');
    envFilter.innerHTML = '<option value="">All Environments</option>' +
        environments.map(env => `<option value="${env.id}">${env.name}</option>`).join('');
}

async function deleteEnvironment(envId) {
    if (!confirm('Are you sure? This will remove the environment from all links.')) return;
    try {
        const response = await fetch(`/api/environments/${envId}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Environment deleted', 'success');
            loadEnvironmentsList();
            loadLinks();
        }
    } catch (error) {
        showNotification('Error deleting environment', 'error');
    }
}

async function loadEnvironments() {
    try {
        const response = await fetch('/api/environments');
        const environments = await response.json();
        updateEnvironmentDropdowns(environments);
    } catch (error) {
        console.error('Error loading environments:', error);
    }
}

let currentTaskForReminder = null;

async function openReminderModal(taskId, taskTitle, deadline) {
    currentTaskForReminder = { id: taskId, title: taskTitle, deadline: deadline };
    document.getElementById('reminder-task-title').textContent = taskTitle;
    document.getElementById('task-reminder-modal').classList.add('active');
    await loadTaskReminders(taskId);
}

async function loadTaskReminders(taskId) {
    const container = document.getElementById('task-reminders-list');
    container.innerHTML = '<div class="spinner"></div>';
    try {
        const response = await fetch(`/api/tasks/${taskId}/reminders`);
        const reminders = await response.json();
        if (reminders.length === 0) {
            container.innerHTML = '<p style="color: #64748b; text-align: center; padding: 20px;">No reminders set for this task</p>';
        } else {
            container.innerHTML = reminders.map(reminder => {
                let reminderText = '';
                if (reminder.reminder_type === 'before_deadline') {
                    const intervals = { 15: '15 minutes', 30: '30 minutes', 60: '1 hour', 180: '3 hours' };
                    reminderText = `⏰ ${intervals[reminder.interval_minutes]} before deadline`;
                } else if (reminder.reminder_type === 'daily') {
                    const time = new Date(reminder.custom_time);
                    reminderText = `📅 Daily at ${time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
                } else if (reminder.reminder_type === 'custom') {
                    const time = new Date(reminder.custom_time);
                    reminderText = `🔔 ${time.toLocaleString()}`;
                }
                return `
                    <div class="reminder-item" style="display: flex; align-items: center; justify-content: space-between; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 10px; ${!reminder.is_active ? 'opacity: 0.5;' : ''}">
                        <div style="flex: 1;">
                            <div style="font-weight: 500;">${reminderText}</div>
                            ${reminder.last_triggered ? `<div style="font-size: 12px; color: #64748b; margin-top: 4px;">Last triggered: ${new Date(reminder.last_triggered).toLocaleString()}</div>` : ''}
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn btn-sm ${reminder.is_active ? 'btn-warning' : 'btn-secondary'}" onclick="toggleReminderActive(${taskId}, ${reminder.id}, ${!reminder.is_active})" title="${reminder.is_active ? 'Disable' : 'Enable'}">
                                <i class="fas fa-${reminder.is_active ? 'pause' : 'play'}"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteTaskReminder(${taskId}, ${reminder.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        }
    } catch (error) {
        container.innerHTML = '<p style="color: #ef4444;">Error loading reminders</p>';
    }
}

async function addQuickReminder(minutes) {
    if (!currentTaskForReminder || !currentTaskForReminder.deadline) {
        showNotification('This task needs a deadline to set before-deadline reminders', 'warning');
        return;
    }
    try {
        const response = await fetch(`/api/tasks/${currentTaskForReminder.id}/reminders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reminder_type: 'before_deadline', interval_minutes: minutes })
        });
        if (response.ok) {
            showNotification('Reminder added successfully!', 'success');
            await loadTaskReminders(currentTaskForReminder.id);
        } else {
            const error = await response.json();
            showNotification(`Error: ${error.error}`, 'error');
        }
    } catch (error) {
        showNotification('Error adding reminder', 'error');
    }
}

async function addDailyReminder() {
    const timeInput = document.getElementById('daily-reminder-time').value;
    if (!timeInput) {
        showNotification('Please select a time for daily reminder', 'warning');
        return;
    }
    const today = new Date();
    const [hours, minutes] = timeInput.split(':');
    today.setHours(parseInt(hours), parseInt(minutes), 0, 0);
    try {
        const response = await fetch(`/api/tasks/${currentTaskForReminder.id}/reminders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reminder_type: 'daily', custom_time: today.toISOString() })
        });
        if (response.ok) {
            showNotification('Daily reminder added successfully!', 'success');
            document.getElementById('daily-reminder-time').value = '';
            await loadTaskReminders(currentTaskForReminder.id);
        } else {
            const error = await response.json();
            showNotification(`Error: ${error.error}`, 'error');
        }
    } catch (error) {
        showNotification('Error adding daily reminder', 'error');
    }
}

async function addCustomReminder() {
    const datetimeInput = document.getElementById('custom-reminder-datetime').value;
    if (!datetimeInput) {
        showNotification('Please select a date and time for custom reminder', 'warning');
        return;
    }
    const customTime = new Date(datetimeInput);
    try {
        const response = await fetch(`/api/tasks/${currentTaskForReminder.id}/reminders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reminder_type: 'custom', custom_time: customTime.toISOString() })
        });
        if (response.ok) {
            showNotification('Custom reminder added successfully!', 'success');
            document.getElementById('custom-reminder-datetime').value = '';
            await loadTaskReminders(currentTaskForReminder.id);
        } else {
            const error = await response.json();
            showNotification(`Error: ${error.error}`, 'error');
        }
    } catch (error) {
        showNotification('Error adding custom reminder', 'error');
    }
}

async function toggleReminderActive(taskId, reminderId, isActive) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/reminders/${reminderId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: isActive })
        });
        if (response.ok) {
            showNotification(`Reminder ${isActive ? 'enabled' : 'disabled'}`, 'success');
            await loadTaskReminders(taskId);
        }
    } catch (error) {
        showNotification('Error updating reminder', 'error');
    }
}

async function deleteTaskReminder(taskId, reminderId) {
    if (!confirm('Are you sure you want to delete this reminder?')) return;
    try {
        const response = await fetch(`/api/tasks/${taskId}/reminders/${reminderId}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Reminder deleted successfully', 'success');
            await loadTaskReminders(taskId);
        }
    } catch (error) {
        showNotification('Error deleting reminder', 'error');
    }
}

function closeReminderModal() {
    document.getElementById('task-reminder-modal').classList.remove('active');
    currentTaskForReminder = null;
}

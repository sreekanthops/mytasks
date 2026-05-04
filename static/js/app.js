// Global state
let currentSection = 'github';
let reminderCheckInterval = null;

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
});

// Request notification permission
async function requestNotificationPermission() {
    if ('Notification' in window) {
        if (Notification.permission === 'default') {
            const permission = await Notification.requestPermission();
            if (permission === 'granted') {
                showNotification('Notifications enabled! You will receive reminder alerts.', 'success');
            } else {
                showNotification('Please enable notifications in your browser settings to receive reminder alerts.', 'warning');
            }
        } else if (Notification.permission === 'denied') {
            showNotification('Notifications are blocked. Please enable them in browser settings.', 'warning');
        }
    }
}

// Start checking reminders every minute
function startReminderChecker() {
    // Check immediately
    checkReminders();
    // Then check every 30 seconds
    reminderCheckInterval = setInterval(checkReminders, 30000);
}

// Check for due reminders
async function checkReminders() {
    try {
        const response = await fetch('/api/reminders');
        const reminders = await response.json();
        
        const now = new Date();
        reminders.forEach(reminder => {
            const reminderTime = new Date(reminder.reminder_time);
            const timeDiff = reminderTime - now;
            
            // Show notification if reminder is due (within 1 minute) or overdue
            if (timeDiff <= 60000 && timeDiff >= -60000) {
                showReminderNotification(reminder);
            }
            // Show upcoming reminder (5 minutes before)
            else if (timeDiff > 0 && timeDiff <= 300000) {
                const minutesLeft = Math.ceil(timeDiff / 60000);
                showUpcomingReminder(reminder, minutesLeft);
            }
        });
    } catch (error) {
        console.error('Error checking reminders:', error);
    }
}

// Show reminder notification
function showReminderNotification(reminder) {
    // Play sound
    playNotificationSound();
    
    // Browser notification
    if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification('⏰ Reminder Due!', {
            body: reminder.title + (reminder.description ? '\n' + reminder.description : ''),
            icon: '/static/favicon.ico',
            badge: '/static/favicon.ico',
            tag: `reminder-${reminder.id}`,
            requireInteraction: true
        });
        
        notification.onclick = function() {
            window.focus();
            switchSection('reminders');
            notification.close();
        };
    }
    
    // In-app notification
    showInAppNotification(reminder, 'due');
}

// Show upcoming reminder
function showUpcomingReminder(reminder, minutesLeft) {
    // Only show once per reminder
    const notifiedKey = `notified-${reminder.id}`;
    if (sessionStorage.getItem(notifiedKey)) {
        return;
    }
    sessionStorage.setItem(notifiedKey, 'true');
    
    if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification('⏰ Upcoming Reminder', {
            body: `${reminder.title} in ${minutesLeft} minute${minutesLeft > 1 ? 's' : ''}`,
            icon: '/static/favicon.ico',
            tag: `reminder-upcoming-${reminder.id}`
        });
        
        notification.onclick = function() {
            window.focus();
            switchSection('reminders');
            notification.close();
        };
    }
}

// Play notification sound
function playNotificationSound() {
    // Create audio context for notification sound
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
    
    // Play twice
    setTimeout(() => {
        const oscillator2 = audioContext.createOscillator();
        const gainNode2 = audioContext.createGain();
        
        oscillator2.connect(gainNode2);
        gainNode2.connect(audioContext.destination);
        
        oscillator2.frequency.value = 1000;
        oscillator2.type = 'sine';
        
        gainNode2.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator2.start(audioContext.currentTime);
        oscillator2.stop(audioContext.currentTime + 0.5);
    }, 200);
}

// Show in-app notification
function showInAppNotification(reminder, type) {
    const notification = document.createElement('div');
    notification.className = 'toast-notification';
    notification.innerHTML = `
        <div class="toast-header">
            <i class="fas fa-bell"></i>
            <strong>${type === 'due' ? 'Reminder Due!' : 'Upcoming Reminder'}</strong>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
        <div class="toast-body">
            <strong>${reminder.title}</strong>
            ${reminder.description ? `<p>${reminder.description}</p>` : ''}
            <small>${new Date(reminder.reminder_time).toLocaleString()}</small>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 10 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 10000);
}

// Navigation
function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.dataset.section;
            switchSection(section);
        });
    });
}

function switchSection(section) {
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-section="${section}"]`).classList.add('active');

    // Update content sections
    document.querySelectorAll('.content-section').forEach(sec => {
        sec.classList.remove('active');
    });
    document.getElementById(`${section}-section`).classList.add('active');

    // Update title
    const titles = {
        'github': 'GitHub Issues',
        'tasks': 'My Tasks',
        'reminders': 'Reminders',
        'links': 'Dashboard Links',
        'settings': 'Settings'
    };
    document.getElementById('section-title').textContent = titles[section];

    currentSection = section;

    // Load data for the section
    switch(section) {
        case 'github':
            loadGithubIssues();
            break;
        case 'tasks':
            loadTasks();
            break;
        case 'reminders':
            loadReminders();
            break;
        case 'links':
            loadLinks();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// Time display
function updateTime() {
    const now = new Date();
    const options = { 
        weekday: 'short', 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    document.getElementById('current-time').textContent = now.toLocaleDateString('en-US', options);
}

// GitHub Issues
async function loadGithubIssues() {
    const container = document.getElementById('github-issues');
    const status = document.getElementById('github-status').value;
    
    container.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i> Loading issues...</div>';
    
    try {
        const response = await fetch(`/api/github/issues?status=${status}`);
        const data = await response.json();
        
        if (response.ok) {
            // Cache for import functionality
            githubIssuesCache = data;
            
            if (data.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fab fa-github"></i>
                        <p>No ${status} issues found</p>
                    </div>
                `;
            } else {
                container.innerHTML = data.map(issue => `
                    <div class="card">
                        <div class="card-header">
                            <div>
                                <div class="card-title">#${issue.number} ${issue.title}</div>
                                <div class="card-meta">
                                    <span class="badge badge-${issue.state}">${issue.state}</span>
                                    ${issue.labels.map(label => `<span class="badge" style="background: #${label.color}20; color: #${label.color}">${label.name}</span>`).join('')}
                                </div>
                            </div>
                        </div>
                        <div class="card-description">${issue.body ? issue.body.substring(0, 150) + '...' : 'No description'}</div>
                        <div class="card-footer">
                            <span class="card-time">Created: ${new Date(issue.created_at).toLocaleDateString()}</span>
                            <a href="${issue.html_url}" target="_blank" class="btn btn-primary">
                                <i class="fas fa-external-link-alt"></i> View
                            </a>
                        </div>
                    </div>
                `).join('');
            }
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>${data.error || 'Failed to load GitHub issues'}</p>
                    <p style="font-size: 14px; margin-top: 10px;">Please configure your GitHub token in Settings</p>
                </div>
            `;
        }
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Error loading issues: ${error.message}</p>
            </div>
        `;
    }
}

// Tasks
async function loadTasks() {
    const container = document.getElementById('tasks-list');
    const filter = document.getElementById('task-filter').value;
    
    container.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i> Loading tasks...</div>';
    
    try {
        const url = filter ? `/api/tasks?status=${filter}` : '/api/tasks';
        const response = await fetch(url);
        const tasks = await response.json();
        
        if (tasks.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-tasks"></i>
                    <p>No tasks found</p>
                </div>
            `;
        } else {
            container.innerHTML = tasks.map(task => `
                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">${task.title}</div>
                            <div class="card-meta">
                                <span class="badge badge-${task.status}">${task.status}</span>
                                ${task.due_date ? `<span class="badge"><i class="fas fa-calendar"></i> ${new Date(task.due_date).toLocaleDateString()}</span>` : ''}
                            </div>
                        </div>
                    </div>
                    ${task.description ? `<div class="card-description">${task.description}</div>` : ''}
                    <div class="card-footer">
                        <span class="card-time">Created: ${new Date(task.created_at).toLocaleDateString()}</span>
                        <div class="card-actions">
                            <select class="control-select" onchange="updateTaskStatus(${task.id}, this.value)" style="padding: 6px 12px; font-size: 12px;">
                                <option value="pending" ${task.status === 'pending' ? 'selected' : ''}>Pending</option>
                                <option value="inprogress" ${task.status === 'inprogress' ? 'selected' : ''}>In Progress</option>
                                <option value="hold" ${task.status === 'hold' ? 'selected' : ''}>On Hold</option>
                                <option value="done" ${task.status === 'done' ? 'selected' : ''}>Done</option>
                                <option value="archive" ${task.status === 'archive' ? 'selected' : ''}>Archive</option>
                            </select>
                            <button class="btn btn-danger" onclick="deleteTask(${task.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Error loading tasks: ${error.message}</p>
            </div>
        `;
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
            showNotification('Task deleted', 'success');
            loadTasks();
        }
    } catch (error) {
        showNotification('Error deleting task', 'error');
    }
}

// Reminders
async function loadReminders() {
    const container = document.getElementById('reminders-list');
    
    container.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i> Loading reminders...</div>';
    
    try {
        const response = await fetch('/api/reminders');
        const reminders = await response.json();
        
        if (reminders.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-bell"></i>
                    <p>No active reminders</p>
                </div>
            `;
        } else {
            container.innerHTML = reminders.map(reminder => {
                const reminderDate = new Date(reminder.reminder_time);
                const isPast = reminderDate < new Date();
                
                return `
                    <div class="card">
                        <div class="card-header">
                            <div>
                                <div class="card-title">${reminder.title}</div>
                                <div class="card-meta">
                                    <span class="badge ${isPast ? 'badge-hold' : 'badge-pending'}">
                                        <i class="fas fa-clock"></i> ${reminderDate.toLocaleString()}
                                    </span>
                                </div>
                            </div>
                        </div>
                        ${reminder.description ? `<div class="card-description">${reminder.description}</div>` : ''}
                        <div class="card-footer">
                            <span class="card-time">Created: ${new Date(reminder.created_at).toLocaleDateString()}</span>
                            <button class="btn btn-danger" onclick="dismissReminder(${reminder.id})">
                                <i class="fas fa-check"></i> Dismiss
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        }
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Error loading reminders: ${error.message}</p>
            </div>
        `;
    }
}

async function dismissReminder(reminderId) {
    try {
        const response = await fetch(`/api/reminders/${reminderId}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Reminder dismissed', 'success');
            loadReminders();
        }
    } catch (error) {
        showNotification('Error dismissing reminder', 'error');
    }
}

// Links
async function loadLinks(search = '') {
    const container = document.getElementById('links-list');
    
    container.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i> Loading links...</div>';
    
    try {
        const url = search ? `/api/links?search=${encodeURIComponent(search)}` : '/api/links';
        const response = await fetch(url);
        const links = await response.json();
        
        if (links.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-link"></i>
                    <p>No links found</p>
                </div>
            `;
        } else {
            container.innerHTML = links.map(link => `
                <div class="card link-card" onclick="window.open('${link.url}', '_blank')">
                    <div class="card-header">
                        <div>
                            <div class="card-title">${link.name}</div>
                            <div class="link-url">${link.url}</div>
                        </div>
                    </div>
                    ${link.description ? `<div class="card-description">${link.description}</div>` : ''}
                    <div class="card-footer">
                        <span class="card-time">Added: ${new Date(link.created_at).toLocaleDateString()}</span>
                        <button class="btn btn-danger" onclick="event.stopPropagation(); deleteLink(${link.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Error loading links: ${error.message}</p>
            </div>
        `;
    }
}

function searchLinks() {
    const search = document.getElementById('link-search').value;
    loadLinks(search);
}

async function deleteLink(linkId) {
    if (!confirm('Are you sure you want to delete this link?')) return;
    
    try {
        const response = await fetch(`/api/links/${linkId}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Link deleted', 'success');
            loadLinks();
        }
    } catch (error) {
        showNotification('Error deleting link', 'error');
    }
}

// Settings
async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const settings = await response.json();
        
        document.getElementById('github-username').value = settings.github_username || '';
        document.getElementById('github-token').placeholder = settings.has_token ? 'Token configured (hidden)' : 'Enter your GitHub token';
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

async function saveSettings() {
    const username = document.getElementById('github-username').value;
    const token = document.getElementById('github-token').value;
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                github_username: username,
                github_token: token || undefined
            })
        });
        
        if (response.ok) {
            showNotification('Settings saved successfully', 'success');
            document.getElementById('github-token').value = '';
            loadSettings();
        }
    } catch (error) {
        showNotification('Error saving settings', 'error');
    }
}

// Modal handlers
function showAddTaskModal() {
    document.getElementById('task-modal').classList.add('active');
}

function showAddReminderModal() {
    document.getElementById('reminder-modal').classList.add('active');
}

function showAddLinkModal() {
    document.getElementById('link-modal').classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Form handlers
function setupFormHandlers() {
    // Task form
    document.getElementById('task-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const data = {
            title: document.getElementById('task-title').value,
            description: document.getElementById('task-description').value,
            status: document.getElementById('task-status').value,
            due_date: document.getElementById('task-due-date').value || null
        };
        
        try {
            const response = await fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                showNotification('Task added successfully', 'success');
                closeModal('task-modal');
                this.reset();
                loadTasks();
            }
        } catch (error) {
            showNotification('Error adding task', 'error');
        }
    });
    
    // Reminder form
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
                showNotification('Reminder added successfully', 'success');
                closeModal('reminder-modal');
                this.reset();
                loadReminders();
            }
        } catch (error) {
            showNotification('Error adding reminder', 'error');
        }
    });
    
    // Link form
    document.getElementById('link-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const data = {
            name: document.getElementById('link-name').value,
            url: document.getElementById('link-url').value,
            description: document.getElementById('link-description').value
        };
        
        try {
            const response = await fetch('/api/links', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                showNotification('Link added successfully', 'success');
                closeModal('link-modal');
                this.reset();
                loadLinks();
            }
        } catch (error) {
            showNotification('Error adding link', 'error');
        }
    });
}

// Notification system
function showNotification(message, type) {
    // Simple alert for now - can be enhanced with a toast notification system
    alert(message);
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
}

// Made with Bob

// GitHub Issues cache for import
let githubIssuesCache = [];

// GitHub Import Functions
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
            select.innerHTML = issues.map(issue => 
                `<option value="${issue.number}">#${issue.number} - ${issue.title}</option>`
            ).join('');
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
        const response = await fetch(`/api/tasks/from-github/${issueNumber}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showNotification('GitHub issue imported as task!', 'success');
            closeModal('github-import-modal');
            switchSection('tasks');
        } else {
            const error = await response.json();
            showNotification(`Error: ${error.error}`, 'error');
        }
    } catch (error) {
        showNotification('Error importing issue', 'error');
    }
}

// Environment Management Functions
async function showManageEnvModal() {
    const modal = document.getElementById('env-modal');
    modal.classList.add('active');
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
                    <button class="btn btn-danger" onclick="deleteEnvironment(${env.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `).join('');
        }
        
        // Update environment dropdowns
        updateEnvironmentDropdowns(environments);
    } catch (error) {
        container.innerHTML = '<p style="color: #ef4444;">Error loading environments</p>';
    }
}

function updateEnvironmentDropdowns(environments) {
    const linkEnvSelect = document.getElementById('link-environment');
    const envFilter = document.getElementById('env-filter');
    
    // Update link form dropdown
    linkEnvSelect.innerHTML = '<option value="">No Environment</option>' + 
        environments.map(env => `<option value="${env.id}">${env.name}</option>`).join('');
    
    // Update filter dropdown
    envFilter.innerHTML = '<option value="">All Environments</option>' + 
        environments.map(env => `<option value="${env.id}">${env.name}</option>`).join('');
}

async function deleteEnvironment(envId) {
    if (!confirm('Delete this environment? Links will not be deleted, just unassigned.')) return;
    
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

// Update loadLinks to support environment filtering
async function loadLinks(search = '') {
    const container = document.getElementById('links-list');
    const envFilter = document.getElementById('env-filter');
    const envId = envFilter ? envFilter.value : '';
    
    container.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i> Loading links...</div>';
    
    try {
        let url = '/api/links?';
        if (search) url += `search=${encodeURIComponent(search)}&`;
        if (envId) url += `environment_id=${envId}`;
        
        const response = await fetch(url);
        const links = await response.json();
        
        if (links.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-link"></i>
                    <p>No links found</p>
                </div>
            `;
        } else {
            container.innerHTML = links.map(link => `
                <div class="card link-card" onclick="window.open('${link.url}', '_blank')">
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
                        <button class="btn btn-danger" onclick="event.stopPropagation(); deleteLink(${link.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Error loading links: ${error.message}</p>
            </div>
        `;
    }
}

// Load environments on init
document.addEventListener('DOMContentLoaded', function() {
    loadEnvironments();
});

async function loadEnvironments() {
    try {
        const response = await fetch('/api/environments');
        const environments = await response.json();
        updateEnvironmentDropdowns(environments);
    } catch (error) {
        console.error('Error loading environments:', error);
    }
}


// Update form handlers to include environment support
document.addEventListener('DOMContentLoaded', function() {
    // Environment form
    document.getElementById('env-form').addEventListener('submit', async function(e) {
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
                showNotification('Environment created successfully', 'success');
                this.reset();
                loadEnvironmentsList();
            }
        } catch (error) {
            showNotification('Error creating environment', 'error');
        }
    });
    
    // Update link form to include environment
    const originalLinkFormHandler = document.getElementById('link-form').onsubmit;
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
                showNotification('Link added successfully', 'success');
                closeModal('link-modal');
                this.reset();
                loadLinks();
            }
        } catch (error) {
            showNotification('Error adding link', 'error');
        }
    });
});

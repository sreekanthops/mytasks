// Reminders page JavaScript
let lastNotifiedReminders = new Set();
let lastNotifiedUrgentTasks = new Set();

document.addEventListener('DOMContentLoaded', function() {
    // Request notification permission
    requestNotificationPermission();
    
    loadAllReminders();
    loadGithubIssuesForDropdown();
    
    const reminderForm = document.getElementById('reminder-form');
    if (reminderForm) {
        reminderForm.addEventListener('submit', handleReminderSubmit);
    }
    
    // Setup GitHub issue dropdown change
    const githubIssueSelect = document.getElementById('reminder-github-issue');
    if (githubIssueSelect) {
        githubIssueSelect.addEventListener('change', handleGithubIssueSelect);
    }
    
    // Refresh reminders every 30 seconds
    setInterval(loadAllReminders, 30000);
});

// Request notification permission
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                console.log('Notification permission granted');
            }
        });
    }
}

// Show desktop notification
function showDesktopNotification(title, body, icon = '🔔') {
    if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification(title, {
            body: body,
            icon: '/static/favicon.ico',
            badge: '/static/favicon.ico',
            tag: title, // Prevents duplicate notifications
            requireInteraction: true // Notification stays until user interacts
        });
        
        notification.onclick = function() {
            window.focus();
            notification.close();
        };
    }
}

async function loadAllReminders() {
    try {
        // Load both user reminders and urgent tasks
        const [remindersResponse, tasksResponse] = await Promise.all([
            fetch('/api/reminders'),
            fetch('/api/tasks')
        ]);
        
        const reminders = await remindersResponse.json();
        const tasks = await tasksResponse.json();
        
        displayAllReminders(reminders, tasks);
    } catch (error) {
        console.error('Error loading reminders:', error);
    }
}

function displayAllReminders(reminders, tasks) {
    const list = document.getElementById('reminders-list');
    if (!list) return;
    
    // Filter urgent tasks (deadline < 1 day and not completed/archived/snoozed)
    const now = new Date();
    const oneDayFromNow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
    
    const urgentTasks = tasks.filter(task => {
        if (!task.deadline || task.status === 'done' || task.status === 'archive') {
            return false;
        }
        
        // Check if task is snoozed
        if (task.mute_until) {
            const muteUntil = new Date(task.mute_until);
            if (muteUntil > now) {
                return false; // Task is snoozed
            }
        }
        
        const deadline = new Date(task.deadline);
        return deadline <= oneDayFromNow;
    });
    
    // Show desktop notifications for new urgent tasks
    urgentTasks.forEach(task => {
        if (!lastNotifiedUrgentTasks.has(task.id)) {
            const deadline = new Date(task.deadline);
            const timeLeft = deadline - now;
            const hoursLeft = Math.floor(timeLeft / (1000 * 60 * 60));
            const isOverdue = timeLeft < 0;
            
            let notificationBody = `Deadline: ${deadline.toLocaleString()}`;
            if (isOverdue) {
                notificationBody = `⚠️ OVERDUE! ${notificationBody}`;
            } else {
                notificationBody = `⏰ ${hoursLeft} hours left - ${notificationBody}`;
            }
            
            showDesktopNotification(
                `🚨 Urgent Task: ${task.title}`,
                notificationBody
            );
            lastNotifiedUrgentTasks.add(task.id);
        }
    });
    
    // Show desktop notifications for due reminders (within 5 minutes)
    const fiveMinutesFromNow = new Date(now.getTime() + 5 * 60 * 1000);
    reminders.forEach(reminder => {
        const reminderTime = new Date(reminder.reminder_time);
        if (reminderTime <= fiveMinutesFromNow && reminderTime >= now && !lastNotifiedReminders.has(reminder.id)) {
            const minutesLeft = Math.floor((reminderTime - now) / (1000 * 60));
            showDesktopNotification(
                `📅 Reminder: ${reminder.title}`,
                `Due in ${minutesLeft} minute${minutesLeft !== 1 ? 's' : ''} - ${reminderTime.toLocaleString()}`
            );
            lastNotifiedReminders.add(reminder.id);
        }
    });
    
    // Clean up old notifications from tracking
    const currentUrgentIds = new Set(urgentTasks.map(t => t.id));
    lastNotifiedUrgentTasks = new Set([...lastNotifiedUrgentTasks].filter(id => currentUrgentIds.has(id)));
    
    const currentReminderIds = new Set(reminders.map(r => r.id));
    lastNotifiedReminders = new Set([...lastNotifiedReminders].filter(id => currentReminderIds.has(id)));
    
    let html = '';
    
    // Display urgent tasks section
    if (urgentTasks.length > 0) {
        html += '<div class="reminders-section"><h2 style="color: #ef4444; margin-bottom: 20px;">🚨 Urgent Tasks (< 1 Day)</h2>';
        urgentTasks.forEach(task => {
            const deadline = new Date(task.deadline);
            const timeLeft = deadline - now;
            const hoursLeft = Math.floor(timeLeft / (1000 * 60 * 60));
            const isOverdue = timeLeft < 0;
            
            html += `
                <div class="reminder-card urgent-task ${isOverdue ? 'overdue' : ''}" style="border-left: 4px solid #ef4444; animation: ${isOverdue || hoursLeft < 3 ? 'blink 1s infinite' : 'none'};">
                    <div style="display: flex; justify-content: space-between; align-items: start; gap: 15px;">
                        <div style="flex: 1;">
                            <h3 style="color: #ef4444;">
                                ${isOverdue ? '⚠️ OVERDUE' : '🔴'} ${task.title}
                            </h3>
                            ${task.description ? `<p>${task.description}</p>` : ''}
                            <div class="reminder-time" style="color: ${isOverdue ? '#ef4444' : '#f59e0b'}; font-weight: bold;">
                                ⏰ Deadline: ${deadline.toLocaleString()}
                                ${isOverdue ? ' (OVERDUE!)' : ` (${hoursLeft}h left)`}
                            </div>
                            ${task.reminder_count > 0 ? `<div style="margin-top: 8px; color: var(--text-secondary);"><i class="fas fa-bell"></i> ${task.reminder_count} reminder${task.reminder_count > 1 ? 's' : ''} set</div>` : ''}
                            
                            <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap;">
                                <button class="btn btn-sm" style="background: #6366f1; color: white;" onclick="snoozeTask(${task.id}, 15)">
                                    <i class="fas fa-clock"></i> 15min
                                </button>
                                <button class="btn btn-sm" style="background: #6366f1; color: white;" onclick="snoozeTask(${task.id}, 30)">
                                    <i class="fas fa-clock"></i> 30min
                                </button>
                                <button class="btn btn-sm" style="background: #6366f1; color: white;" onclick="snoozeTask(${task.id}, 60)">
                                    <i class="fas fa-clock"></i> 1hr
                                </button>
                                <button class="btn btn-sm" style="background: #8b5cf6; color: white;" onclick="snoozeTaskCustom(${task.id})">
                                    <i class="fas fa-calendar"></i> Custom
                                </button>
                            </div>
                        </div>
                        <button class="btn btn-primary btn-sm" onclick="window.location.href='/tasks'" style="margin-left: 10px; white-space: nowrap;">
                            View Task
                        </button>
                    </div>
                </div>
            `;
        });
        html += '</div>';
    }
    
    // Display user-set reminders section
    if (reminders.length > 0) {
        html += '<div class="reminders-section" style="margin-top: 30px;"><h2 style="margin-bottom: 20px;">📅 Your Reminders</h2>';
        reminders.forEach(r => {
            const reminderTime = new Date(r.reminder_time);
            const isPast = reminderTime < now;
            
            html += `
                <div class="reminder-card" style="border-left: 4px solid #3b82f6;">
                    <h3>${r.title}</h3>
                    ${r.description ? `<p>${r.description}</p>` : ''}
                    <div class="reminder-time" style="color: ${isPast ? '#ef4444' : 'var(--text-secondary)'};">
                        ⏰ ${reminderTime.toLocaleString()} ${isPast ? '(Past due)' : ''}
                    </div>
                    <button class="btn btn-danger btn-sm" onclick="deleteReminder(${r.id})" style="margin-top: 10px;">
                        Delete
                    </button>
                </div>
            `;
        });
        html += '</div>';
    }
    
    if (urgentTasks.length === 0 && reminders.length === 0) {
        list.innerHTML = '<div class="empty-state"><p>No reminders or urgent tasks</p></div>';
    } else {
        list.innerHTML = html;
    }
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

// Load GitHub issues for dropdown
async function loadGithubIssuesForDropdown() {
    try {
        const response = await fetch('/api/github/issues?status=open');
        const issues = await response.json();
        
        const select = document.getElementById('reminder-github-issue');
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
        const titleInput = document.getElementById('reminder-title');
        if (titleInput && !titleInput.value) {
            titleInput.value = `Reminder: ${selectedOption.dataset.title}`;
        }
    }
}


// Snooze task for specific minutes
async function snoozeTask(taskId, minutes) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/snooze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ minutes })
        });
        
        if (response.ok) {
            showNotification(`Task snoozed for ${minutes} minutes`, 'success');
            loadAllReminders();
            // Update urgent count
            if (typeof updateUrgentCount === 'function') {
                updateUrgentCount();
            }
        } else {
            throw new Error('Failed to snooze task');
        }
    } catch (error) {
        console.error('Error snoozing task:', error);
        showNotification('Failed to snooze task', 'error');
    }
}

// Snooze task with custom time
async function snoozeTaskCustom(taskId) {
    const customTime = prompt('Enter snooze time (e.g., 2026-05-04T18:00):');
    if (!customTime) return;
    
    try {
        const response = await fetch(`/api/tasks/${taskId}/snooze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ custom_time: customTime })
        });
        
        if (response.ok) {
            showNotification('Task snoozed until ' + new Date(customTime).toLocaleString(), 'success');
            loadAllReminders();
            // Update urgent count
            if (typeof updateUrgentCount === 'function') {
                updateUrgentCount();
            }
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to snooze task');
        }
    } catch (error) {
        console.error('Error snoozing task:', error);
        showNotification(error.message || 'Failed to snooze task', 'error');
    }
}

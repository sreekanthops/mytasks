// Add this code to app.js after the startReminderChecker function (around line 43)

// Add to the reminder checker interval
function startReminderChecker() {
    checkReminders();
    checkDeadlineReminders();
    checkTaskReminders(); // ADD THIS LINE
    reminderCheckInterval = setInterval(() => {
        checkReminders();
        checkDeadlineReminders();
        checkTaskReminders(); // ADD THIS LINE
    }, 30000);
}

// Add these functions after checkDeadlineReminders function (around line 82)

// Check for task-specific reminders
async function checkTaskReminders() {
    try {
        const response = await fetch('/api/task-reminders/check');
        const taskReminders = await response.json();
        
        taskReminders.forEach(reminder => {
            showTaskReminderNotification(reminder);
        });
    } catch (error) {
        console.error('Error checking task reminders:', error);
    }
}

// Show task reminder notification
function showTaskReminderNotification(reminder) {
    playNotificationSound();
    
    if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification(reminder.message, {
            body: `Priority: ${reminder.priority}\nClick to view task`,
            icon: '/static/favicon.ico',
            badge: '/static/favicon.ico',
            tag: `task-reminder-${reminder.reminder_id}`,
            requireInteraction: true,
            data: { taskId: reminder.task_id, url: reminder.github_issue_url }
        });
        
        notification.onclick = function() {
            window.focus();
            if (reminder.github_issue_url) {
                window.open(reminder.github_issue_url, '_blank');
            }
            this.close();
        };
    }
    
    const urgency = reminder.priority === 'urgent' ? 'critical' : 'warning';
    showToast(reminder.message, urgency);
}

// Add these functions at the end of the file (before the last closing brace)

// Task Reminder Management Functions
let currentTaskForReminder = null;

async function openReminderModal(taskId, taskTitle, deadline) {
    currentTaskForReminder = { id: taskId, title: taskTitle, deadline: deadline };
    
    const modal = document.getElementById('task-reminder-modal');
    document.getElementById('reminder-task-title').textContent = taskTitle;
    
    modal.classList.add('active');
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
            body: JSON.stringify({
                reminder_type: 'before_deadline',
                interval_minutes: minutes
            })
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
            body: JSON.stringify({
                reminder_type: 'daily',
                custom_time: today.toISOString()
            })
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
            body: JSON.stringify({
                reminder_type: 'custom',
                custom_time: customTime.toISOString()
            })
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
    if (!confirm('Are you sure you want to delete this reminder?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/tasks/${taskId}/reminders/${reminderId}`, {
            method: 'DELETE'
        });
        
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

// ALSO UPDATE THE TASK CARD HTML (in loadTasks function around line 523):
// Change the button section to:
/*
<div class="flex gap-2">
    <button class="btn btn-sm" style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; border: none;" onclick="openReminderModal(${task.id}, '${task.title.replace(/'/g, "\\'")}', ${task.deadline ? `'${task.deadline}'` : 'null'})" title="⏰ Set custom reminders">
        <i class="fas fa-bell"></i> <span style="font-size: 11px;">Reminders</span>
    </button>
    ${task.deadline ? `
        <button class="btn btn-sm ${task.is_muted ? 'btn-secondary' : 'btn-warning'}" onclick="muteTask(${task.id})" title="${task.is_muted ? '🔔 Unmute auto deadline alerts' : '🔕 Mute auto deadline alerts'}">
            <i class="fas fa-bell${task.is_muted ? '' : '-slash'}"></i>
        </button>
    ` : ''}
    <select class="form-control" onchange="updateTaskStatus(${task.id}, this.value)" style="padding: 8px 12px; font-size: 13px; width: auto;">
        ...
    </select>
    ...
</div>
*/

// Made with Bob

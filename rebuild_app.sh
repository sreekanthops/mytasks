#!/bin/bash
# This script will rebuild the complete app.js file

echo "Creating complete app.js with all features..."

# The file is too large to create in one command
# Instead, let's use the working git version and add only the reminder functions

# First, restore the git version
git checkout static/js/app.js

# Now append the reminder functions at the end (before the last line)
# We'll use sed to insert before the last closing brace

# Create a temp file with the reminder functions
cat > /tmp/reminder_functions.js << 'EOF'

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
        const response = await fetch(\`/api/tasks/\${taskId}/reminders\`);
        const reminders = await response.json();
        if (reminders.length === 0) {
            container.innerHTML = '<p style="color: #64748b; text-align: center; padding: 20px;">No reminders set for this task</p>';
        } else {
            container.innerHTML = reminders.map(reminder => {
                let reminderText = '';
                if (reminder.reminder_type === 'before_deadline') {
                    const intervals = { 15: '15 minutes', 30: '30 minutes', 60: '1 hour', 180: '3 hours' };
                    reminderText = \`⏰ \${intervals[reminder.interval_minutes]} before deadline\`;
                } else if (reminder.reminder_type === 'daily') {
                    const time = new Date(reminder.custom_time);
                    reminderText = \`📅 Daily at \${time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}\`;
                } else if (reminder.reminder_type === 'custom') {
                    const time = new Date(reminder.custom_time);
                    reminderText = \`🔔 \${time.toLocaleString()}\`;
                }
                return \`
                    <div class="reminder-item" style="display: flex; align-items: center; justify-content: space-between; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 10px; \${!reminder.is_active ? 'opacity: 0.5;' : ''}">
                        <div style="flex: 1;">
                            <div style="font-weight: 500;">\${reminderText}</div>
                            \${reminder.last_triggered ? \`<div style="font-size: 12px; color: #64748b; margin-top: 4px;">Last triggered: \${new Date(reminder.last_triggered).toLocaleString()}</div>\` : ''}
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn btn-sm \${reminder.is_active ? 'btn-warning' : 'btn-secondary'}" onclick="toggleReminderActive(\${taskId}, \${reminder.id}, \${!reminder.is_active})" title="\${reminder.is_active ? 'Disable' : 'Enable'}">
                                <i class="fas fa-\${reminder.is_active ? 'pause' : 'play'}"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteTaskReminder(\${taskId}, \${reminder.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                \`;
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
        const response = await fetch(\`/api/tasks/\${currentTaskForReminder.id}/reminders\`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reminder_type: 'before_deadline', interval_minutes: minutes })
        });
        if (response.ok) {
            showNotification('Reminder added successfully!', 'success');
            await loadTaskReminders(currentTaskForReminder.id);
        } else {
            const error = await response.json();
            showNotification(\`Error: \${error.error}\`, 'error');
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
        const response = await fetch(\`/api/tasks/\${currentTaskForReminder.id}/reminders\`, {
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
            showNotification(\`Error: \${error.error}\`, 'error');
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
        const response = await fetch(\`/api/tasks/\${currentTaskForReminder.id}/reminders\`, {
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
            showNotification(\`Error: \${error.error}\`, 'error');
        }
    } catch (error) {
        showNotification('Error adding custom reminder', 'error');
    }
}

async function toggleReminderActive(taskId, reminderId, isActive) {
    try {
        const response = await fetch(\`/api/tasks/\${taskId}/reminders/\${reminderId}\`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: isActive })
        });
        if (response.ok) {
            showNotification(\`Reminder \${isActive ? 'enabled' : 'disabled'}\`, 'success');
            await loadTaskReminders(taskId);
        }
    } catch (error) {
        showNotification('Error updating reminder', 'error');
    }
}

async function deleteTaskReminder(taskId, reminderId) {
    if (!confirm('Are you sure you want to delete this reminder?')) return;
    try {
        const response = await fetch(\`/api/tasks/\${taskId}/reminders/\${reminderId}\`, { method: 'DELETE' });
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

async function checkTaskReminders() {
    try {
        const response = await fetch('/api/task-reminders/check');
        const taskReminders = await response.json();
        taskReminders.forEach(reminder => {
            playNotificationSound();
            if ('Notification' in window && Notification.permission === 'granted') {
                const notification = new Notification(reminder.message, {
                    body: \`Priority: \${reminder.priority}\\nClick to view task\`,
                    icon: '/static/favicon.ico',
                    tag: \`task-reminder-\${reminder.reminder_id}\`,
                    requireInteraction: true
                });
                notification.onclick = function() {
                    window.focus();
                    if (reminder.github_issue_url) window.open(reminder.github_issue_url, '_blank');
                    this.close();
                };
            }
            const urgency = reminder.priority === 'urgent' ? 'critical' : 'warning';
            showToast(reminder.message, urgency);
        });
    } catch (error) {
        console.error('Error checking task reminders:', error);
    }
}
EOF

# Now insert these functions before the last line of app.js
head -n -1 static/js/app.js > /tmp/app_temp.js
cat /tmp/reminder_functions.js >> /tmp/app_temp.js
tail -n 1 static/js/app.js >> /tmp/app_temp.js

# Replace the original file
mv /tmp/app_temp.js static/js/app.js

# Also need to update the startReminderChecker function to include checkTaskReminders
sed -i.bak 's/checkDeadlineReminders();$/checkDeadlineReminders();\n    checkTaskReminders();/' static/js/app.js
sed -i.bak 's/checkDeadlineReminders();$/checkDeadlineReminders();\n        checkTaskReminders();/2' static/js/app.js

# Verify syntax
if node -c static/js/app.js 2>/dev/null; then
    echo "✅ app.js created successfully and syntax is valid!"
    rm -f static/js/app.js.bak
else
    echo "❌ Syntax error detected, restoring backup"
    mv static/js/app.js.bak static/js/app.js 2>/dev/null || git checkout static/js/app.js
fi


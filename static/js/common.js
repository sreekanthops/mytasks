// Common functionality shared across all pages

// Update time display
function updateTime() {
    const now = new Date();
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = now.toLocaleDateString('en-US', { 
            weekday: 'short', year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        });
    }
}

// Initialize time updates
document.addEventListener('DOMContentLoaded', function() {
    updateTime();
    setInterval(updateTime, 1000);
    requestNotificationPermission();
    startReminderChecker();
    updateUrgentCount();
    // Update urgent count every 30 seconds
    setInterval(updateUrgentCount, 30000);
});

// Update urgent count badge
async function updateUrgentCount() {
    try {
        const response = await fetch('/api/tasks/urgent-count');
        const data = await response.json();
        const badge = document.getElementById('urgent-count-badge');
        if (badge) {
            if (data.count > 0) {
                badge.textContent = data.count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error fetching urgent count:', error);
    }
}

// Request notification permission
async function requestNotificationPermission() {
    if ('Notification' in window) {
        if (Notification.permission === 'default') {
            await Notification.requestPermission();
        }
    }
}

// Start checking reminders
let reminderCheckInterval = null;
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

// Modal functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Made with Bob

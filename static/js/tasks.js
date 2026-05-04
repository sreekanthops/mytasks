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
    
    // Setup event delegation for reminder buttons
    document.addEventListener('click', function(e) {
        const reminderBtn = e.target.closest('.btn-reminder');
        if (reminderBtn) {
            const taskId = reminderBtn.dataset.taskId;
            const taskTitle = reminderBtn.dataset.taskTitle;
            if (taskId && taskTitle) {
                openReminderModal(parseInt(taskId), taskTitle);
            }
        }
    });
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
    
    // Calculate time until deadline
    let deadlineInfo = '';
    let isUrgent = false;
    let hoursLeft = 0;
    let isSnoozed = false;
    
    if (task.deadline) {
        const deadline = new Date(task.deadline);
        const now = new Date();
        const diff = deadline - now;
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const days = Math.floor(hours / 24);
        hoursLeft = hours;
        
        // Check if task is snoozed
        if (task.mute_until) {
            const muteUntil = new Date(task.mute_until);
            if (muteUntil > now) {
                isSnoozed = true;
            }
        }
        
        // Check if task is urgent (< 24 hours or overdue) and not snoozed
        if (task.status !== 'done' && task.status !== 'archive' && !isSnoozed) {
            // Less than 24 hours remaining OR overdue
            if (hours < 24) {
                isUrgent = true;
            }
        }
        
        if (diff > 0) {
            if (days > 0) {
                deadlineInfo = `in ${days} day${days > 1 ? 's' : ''}`;
            } else if (hours > 0) {
                deadlineInfo = `in ${hours} hour${hours > 1 ? 's' : ''}`;
            } else {
                deadlineInfo = 'soon';
            }
        } else {
            deadlineInfo = 'overdue';
        }
    }
    
    return `
        <div class="task-card ${isUrgent ? 'urgent-task' : ''}" data-task-id="${task.id}" style="${isUrgent ? 'border-left: 4px solid #ef4444; animation: blink 1s infinite;' : ''}">
            <div class="task-header">
                <h3>${isUrgent ? '🚨 ' : ''}${task.title}</h3>
                <div class="task-actions">
                    ${isUrgent ? '<button class="siren-button" onclick="window.location.href=\'/reminders\'" title="View in reminders"><i class="fas fa-exclamation-triangle"></i> URGENT</button>' : ''}
                    <button class="btn-icon" onclick="muteTask(${task.id}, ${!task.is_muted})" title="${task.is_muted ? 'Unmute' : 'Mute'} reminders">
                        <i class="fas fa-bell${task.is_muted ? '-slash' : ''}"></i>
                    </button>
                    <button class="btn-icon" onclick="editTask(${task.id})" title="Edit task">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon btn-reminder ${task.reminder_count > 0 ? 'has-reminders' : ''}" data-task-id="${task.id}" data-task-title="${task.title.replace(/"/g, '"')}" title="Manage reminders">
                        <i class="fas fa-clock"></i>
                        ${task.reminder_count > 0 ? `<span class="reminder-badge">${task.reminder_count}</span>` : ''}
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
                ${task.deadline ? `<span class="deadline">⏰ ${new Date(task.deadline).toLocaleString()} ${deadlineInfo ? `<strong>(${deadlineInfo})</strong>` : ''}</span>` : ''}
                ${task.reminder_count > 0 ? `<span class="reminder-info"><i class="fas fa-bell"></i> ${task.reminder_count} reminder${task.reminder_count > 1 ? 's' : ''} set</span>` : ''}
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

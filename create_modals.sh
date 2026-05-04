#!/bin/bash

# Create task_modal.html
cat > templates/modals/task_modal.html << 'EOF'
<!-- Add/Edit Task Modal -->
<div id="task-modal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h3>Add New Task</h3>
            <button class="close-modal" onclick="closeModal('task-modal')">&times;</button>
        </div>
        <form id="task-form">
            <div class="form-group">
                <label for="task-github-issue">🔗 Link to GitHub Issue (Optional)</label>
                <select id="task-github-issue" class="form-control">
                    <option value="">-- No GitHub Issue --</option>
                </select>
                <small style="color: var(--text-secondary); font-size: 12px;">Select a GitHub issue to auto-fill details</small>
            </div>
            
            <div class="form-group">
                <label for="task-title">Title *</label>
                <input type="text" id="task-title" class="form-control" required placeholder="Enter task title">
            </div>
            
            <div class="form-group">
                <label for="task-description">Description</label>
                <textarea id="task-description" class="form-control" rows="3" placeholder="Add task description..."></textarea>
            </div>
            
            <div class="grid grid-2">
                <div class="form-group">
                    <label for="task-status">Status</label>
                    <select id="task-status" class="form-control">
                        <option value="pending">📋 Pending</option>
                        <option value="inprogress">⚡ In Progress</option>
                        <option value="hold">⏸️ On Hold</option>
                        <option value="done">✅ Done</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="task-priority">Priority</label>
                    <select id="task-priority" class="form-control">
                        <option value="low">🟢 Low</option>
                        <option value="medium" selected>🟡 Medium</option>
                        <option value="high">🟠 High</option>
                        <option value="urgent">🔴 Urgent</option>
                    </select>
                </div>
            </div>
            
            <div class="grid grid-2">
                <div class="form-group">
                    <label for="task-deadline">⏰ Deadline *</label>
                    <input type="datetime-local" id="task-deadline" class="form-control" required>
                    <small style="color: var(--text-secondary); font-size: 12px;">You'll be reminded as deadline approaches</small>
                </div>
                
                <div class="form-group">
                    <label for="task-due-date">📅 Due Date</label>
                    <input type="datetime-local" id="task-due-date" class="form-control">
                </div>
            </div>
            
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" onclick="closeModal('task-modal')">Cancel</button>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Add Task
                </button>
            </div>
        </form>
    </div>
</div>
EOF

# Create task_reminder_modal.html
cat > templates/modals/task_reminder_modal.html << 'EOF'
<!-- Task Reminder Modal -->
<div id="task-reminder-modal" class="modal">
    <div class="modal-content" style="max-width: 700px;">
        <div class="modal-header">
            <h2><i class="fas fa-bell"></i> Manage Reminders</h2>
            <button class="close-btn" onclick="closeReminderModal()">&times;</button>
        </div>
        <div class="modal-body">
            <div style="margin-bottom: 20px; padding: 15px; background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%); border-radius: 8px;">
                <h3 style="margin: 0; color: var(--primary);" id="reminder-task-title">Task Title</h3>
            </div>

            <!-- Quick Reminder Options -->
            <div style="margin-bottom: 25px;">
                <h4 style="margin-bottom: 12px; color: var(--text-primary);"><i class="fas fa-clock"></i> Before Deadline</h4>
                <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px;">Get reminded before the task deadline</p>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button class="btn btn-secondary" onclick="addQuickReminder(15)">
                        <i class="fas fa-bell"></i> 15 min before
                    </button>
                    <button class="btn btn-secondary" onclick="addQuickReminder(30)">
                        <i class="fas fa-bell"></i> 30 min before
                    </button>
                    <button class="btn btn-secondary" onclick="addQuickReminder(60)">
                        <i class="fas fa-bell"></i> 1 hour before
                    </button>
                    <button class="btn btn-secondary" onclick="addQuickReminder(180)">
                        <i class="fas fa-bell"></i> 3 hours before
                    </button>
                </div>
            </div>

            <!-- Daily Reminder -->
            <div style="margin-bottom: 25px;">
                <h4 style="margin-bottom: 12px; color: var(--text-primary);"><i class="fas fa-calendar-day"></i> Daily Reminder</h4>
                <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px;">Get reminded every day at a specific time</p>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <input type="time" id="daily-reminder-time" class="form-control" style="flex: 1; max-width: 200px;">
                    <button class="btn btn-primary" onclick="addDailyReminder()">
                        <i class="fas fa-plus"></i> Add Daily Reminder
                    </button>
                </div>
            </div>

            <!-- Custom Reminder -->
            <div style="margin-bottom: 25px;">
                <h4 style="margin-bottom: 12px; color: var(--text-primary);"><i class="fas fa-calendar-alt"></i> Custom Reminder</h4>
                <p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px;">Set a one-time reminder at a specific date and time</p>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <input type="datetime-local" id="custom-reminder-datetime" class="form-control" style="flex: 1; max-width: 250px;">
                    <button class="btn btn-primary" onclick="addCustomReminder()">
                        <i class="fas fa-plus"></i> Add Custom Reminder
                    </button>
                </div>
            </div>

            <!-- Active Reminders List -->
            <div style="margin-top: 30px; padding-top: 20px; border-top: 2px solid var(--border-color);">
                <h4 style="margin-bottom: 15px; color: var(--text-primary);"><i class="fas fa-list"></i> Active Reminders</h4>
                <div id="task-reminders-list">
                    <div class="spinner"></div>
                </div>
            </div>
        </div>
    </div>
</div>
EOF

# Create reminder_modal.html
cat > templates/modals/reminder_modal.html << 'EOF'
<!-- Add Reminder Modal -->
<div id="reminder-modal" class="modal">
    <div class="modal-content">
        <span class="close" onclick="closeModal('reminder-modal')">&times;</span>
        <h2>Add New Reminder</h2>
        <form id="reminder-form">
            <div class="form-group">
                <label for="reminder-title">Title *</label>
                <input type="text" id="reminder-title" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="reminder-description">Description</label>
                <textarea id="reminder-description" class="form-control" rows="3"></textarea>
            </div>
            <div class="form-group">
                <label for="reminder-time">Reminder Time *</label>
                <input type="datetime-local" id="reminder-time" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary">Add Reminder</button>
        </form>
    </div>
</div>
EOF

# Create link_modal.html
cat > templates/modals/link_modal.html << 'EOF'
<!-- Add Link Modal -->
<div id="link-modal" class="modal">
    <div class="modal-content">
        <span class="close" onclick="closeModal('link-modal')">&times;</span>
        <h2>Add New Link</h2>
        <form id="link-form">
            <div class="form-group">
                <label for="link-name">Name *</label>
                <input type="text" id="link-name" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="link-url">URL *</label>
                <input type="url" id="link-url" class="form-control" required>
            </div>
            <div class="form-group">
                <label for="link-description">Description</label>
                <textarea id="link-description" class="form-control" rows="2"></textarea>
            </div>
            <div class="form-group">
                <label for="link-environment">Environment</label>
                <select id="link-environment" class="form-control">
                    <option value="">No Environment</option>
                </select>
            </div>
            <button type="submit" class="btn btn-primary">Add Link</button>
        </form>
    </div>
</div>
EOF

# Create env_modal.html
cat > templates/modals/env_modal.html << 'EOF'
<!-- Manage Environments Modal -->
<div id="env-modal" class="modal">
    <div class="modal-content">
        <span class="close" onclick="closeModal('env-modal')">&times;</span>
        <h2>Manage Environments</h2>
        <form id="env-form" style="margin-bottom: 20px;">
            <div class="form-group">
                <label for="env-name">Environment Name *</label>
                <input type="text" id="env-name" class="form-control" required placeholder="e.g., Production, Staging, Development">
            </div>
            <div class="form-group">
                <label for="env-color">Color</label>
                <input type="color" id="env-color" class="form-control" value="#2563eb">
            </div>
            <button type="submit" class="btn btn-primary">
                <i class="fas fa-plus"></i> Add Environment
            </button>
        </form>
        <hr>
        <h3 style="margin: 20px 0 10px 0;">Existing Environments</h3>
        <div id="env-list"></div>
    </div>
</div>
EOF

echo "✅ Created all modal files"

// Jira Issues Page JavaScript

let jiraIssuesCache = [];

document.addEventListener('DOMContentLoaded', function() {
    loadJiraIssues();
});

async function loadJiraIssues() {
    const container = document.getElementById('jira-issues');
    const status = document.getElementById('jira-status').value;
    container.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i> Loading Jira issues...</div>';
    
    try {
        const response = await fetch(`/api/jira/issues?status=${status}`);
        const data = await response.json();
        
        if (response.ok) {
            jiraIssuesCache = data;
            if (data.length === 0) {
                container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📋</div><h3>No ${status.replace('_', ' ')} issues found</h3><p>All caught up!</p></div>`;
            } else {
                container.innerHTML = data.map(issue => `
                    <div class="card">
                        <div class="card-header">
                            <div>
                                <div class="card-title">${issue.key} - ${issue.summary}</div>
                                <div class="flex gap-2" style="margin-top: 8px;">
                                    <span class="badge badge-${getStatusBadgeClass(issue.status)}">${issue.status}</span>
                                    <span class="badge badge-priority-${issue.priority.toLowerCase()}">${issue.priority}</span>
                                    <span class="badge badge-secondary">${issue.type}</span>
                                </div>
                            </div>
                            <button class="btn btn-sm btn-secondary" onclick="createTaskFromJira('${issue.key}')" title="Create Task">
                                <i class="fas fa-plus"></i> Add to Tasks
                            </button>
                        </div>
                        ${issue.description ? `<div class="card-body">${escapeHtml(issue.description.substring(0, 200))}${issue.description.length > 200 ? '...' : ''}</div>` : ''}
                        <div class="card-footer">
                            <span class="card-time">Updated: ${new Date(issue.updated).toLocaleDateString()}</span>
                            <a href="${issue.url}" target="_blank" class="btn btn-primary"><i class="fas fa-external-link-alt"></i> View in Jira</a>
                        </div>
                    </div>
                `).join('');
            }
        } else {
            container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><h3>Error loading Jira issues</h3><p>${data.error || 'Please configure Jira settings'}</p></div>`;
        }
    } catch (error) {
        container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><h3>Error loading Jira issues</h3><p>${error.message}</p></div>`;
    }
}

function getStatusBadgeClass(status) {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('done') || statusLower.includes('closed') || statusLower.includes('resolved')) {
        return 'done';
    } else if (statusLower.includes('progress') || statusLower.includes('review')) {
        return 'inprogress';
    } else if (statusLower.includes('hold')) {
        return 'hold';
    }
    return 'pending';
}

async function createTaskFromJira(issueKey) {
    if (!confirm(`Create a task from Jira issue ${issueKey}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/tasks/from-jira/${issueKey}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Task created successfully from Jira issue!', 'success');
        } else {
            showNotification(data.error || 'Failed to create task', 'error');
        }
    } catch (error) {
        showNotification('Error creating task: ' + error.message, 'error');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Made with Bob

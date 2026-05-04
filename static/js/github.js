// GitHub Issues Page JavaScript

let githubIssuesCache = [];

document.addEventListener('DOMContentLoaded', function() {
    loadGithubIssues();
});

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

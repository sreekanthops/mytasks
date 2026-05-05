// Settings page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    loadSettings();
    
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', handleSettingsSubmit);
    }
    
    const jiraSettingsForm = document.getElementById('jira-settings-form');
    if (jiraSettingsForm) {
        jiraSettingsForm.addEventListener('submit', handleJiraSettingsSubmit);
    }
});

async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const settings = await response.json();
        
        // Load GitHub settings
        if (settings.github_username) {
            document.getElementById('github-username').value = settings.github_username;
        }
        
        // Load Jira settings
        if (settings.jira_url) {
            document.getElementById('jira-url').value = settings.jira_url;
        }
        if (settings.jira_email) {
            document.getElementById('jira-email').value = settings.jira_email;
        }
        if (settings.jira_project_key) {
            document.getElementById('jira-project-key').value = settings.jira_project_key;
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

async function handleSettingsSubmit(e) {
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
            showNotification('GitHub settings saved successfully', 'success');
        } else {
            throw new Error('Failed to save settings');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showNotification('Failed to save GitHub settings', 'error');
    }
}

async function handleJiraSettingsSubmit(e) {
    e.preventDefault();
    
    const data = {
        jira_url: document.getElementById('jira-url').value,
        jira_email: document.getElementById('jira-email').value,
        jira_api_token: document.getElementById('jira-api-token').value,
        jira_project_key: document.getElementById('jira-project-key').value
    };
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showNotification('Jira settings saved successfully', 'success');
            // Clear the API token field for security
            document.getElementById('jira-api-token').value = '';
        } else {
            throw new Error('Failed to save Jira settings');
        }
    } catch (error) {
        console.error('Error saving Jira settings:', error);
        showNotification('Failed to save Jira settings', 'error');
    }
}

// Links page JavaScript
let allLinks = [];
let currentLinkId = null;
let isEditMode = false;

document.addEventListener('DOMContentLoaded', function() {
    loadLinks();
    loadEnvironments();
    
    const linkForm = document.getElementById('link-form');
    if (linkForm) {
        linkForm.addEventListener('submit', handleLinkSubmit);
    }
    
    const envForm = document.getElementById('env-form');
    if (envForm) {
        envForm.addEventListener('submit', handleEnvSubmit);
    }
});

async function loadLinks() {
    const envFilter = document.getElementById('env-filter')?.value || '';
    try {
        const response = await fetch(`/api/links${envFilter ? '?environment_id=' + envFilter : ''}`);
        allLinks = await response.json();
        displayLinks(allLinks);
    } catch (error) {
        console.error('Error loading links:', error);
    }
}

// Search links
function searchLinks() {
    const searchTerm = document.getElementById('link-search')?.value.toLowerCase() || '';
    const filtered = allLinks.filter(link =>
        link.name.toLowerCase().includes(searchTerm) ||
        link.url.toLowerCase().includes(searchTerm) ||
        (link.description && link.description.toLowerCase().includes(searchTerm))
    );
    displayLinks(filtered);
}

function displayLinks(links) {
    const list = document.getElementById('links-list');
    if (!list) return;
    
    if (links.length === 0) {
        list.innerHTML = '<div class="empty-state"><p>No links found. Create your first dashboard link!</p></div>';
        return;
    }
    
    // Group links by environment
    const grouped = {};
    links.forEach(link => {
        const env = link.environment || 'Others';
        if (!grouped[env]) {
            grouped[env] = [];
        }
        grouped[env].push(link);
    });
    
    // Sort environments (Others last)
    const envNames = Object.keys(grouped).sort((a, b) => {
        if (a === 'Others') return 1;
        if (b === 'Others') return -1;
        return a.localeCompare(b);
    });
    
    list.innerHTML = envNames.map(envName => `
        <div style="margin-bottom: 30px;">
            <h3 style="color: var(--text-primary); margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid var(--border-color); display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-${envName === 'Others' ? 'folder' : 'server'}"></i>
                ${envName}
                <span style="font-size: 14px; color: var(--text-secondary); font-weight: normal;">(${grouped[envName].length})</span>
            </h3>
            ${grouped[envName].map(link => `
                <div class="link-card" style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: var(--shadow-md); transition: transform 0.2s, box-shadow 0.2s;">
                    <div style="display: flex; justify-content: space-between; align-items: start; gap: 15px;">
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                                <i class="fas fa-link" style="color: var(--primary-color); font-size: 20px;"></i>
                                <h3 style="margin: 0;">
                                    <a href="${link.url}" target="_blank" style="color: var(--primary-color); text-decoration: none; font-size: 18px; font-weight: 600;">
                                        ${link.name}
                                    </a>
                                </h3>
                            </div>
                            
                            ${link.description ? `
                                <p style="color: var(--text-secondary); margin: 8px 0 12px 32px; font-size: 14px;">
                                    <i class="fas fa-info-circle" style="margin-right: 6px;"></i>${link.description}
                                </p>
                            ` : ''}
                            
                            <div style="display: flex; align-items: center; gap: 12px; margin-left: 32px; flex-wrap: wrap;">
                                ${link.environment ? `
                                    <span class="env-badge" style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; background: ${link.environment_color || '#6366f1'}; color: white; border-radius: 16px; font-size: 12px; font-weight: 600;">
                                        <i class="fas fa-server"></i> ${link.environment}
                                    </span>
                                ` : '<span style="color: var(--text-secondary); font-size: 12px;"><i class="fas fa-tag"></i> No environment</span>'}
                                
                                <span style="color: var(--text-secondary); font-size: 12px;">
                                    <i class="fas fa-external-link-alt"></i>
                                    <a href="${link.url}" target="_blank" style="color: var(--text-secondary); text-decoration: none; word-break: break-all;">
                                        ${link.url.length > 50 ? link.url.substring(0, 50) + '...' : link.url}
                                    </a>
                                </span>
                            </div>
                        </div>
                        
                        <div style="display: flex; gap: 8px; flex-shrink: 0;">
                            <button class="btn btn-secondary btn-sm" onclick="editLink(${link.id})" title="Edit link">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="deleteLink(${link.id})" title="Delete link">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `).join('');
}

async function loadEnvironments() {
    try {
        const response = await fetch('/api/environments');
        const envs = await response.json();
        
        // Update filter dropdown
        const filter = document.getElementById('env-filter');
        if (filter) {
            filter.innerHTML = '<option value="">All Environments</option>' +
                envs.map(e => `<option value="${e.id}">${e.name}</option>`).join('');
        }
        
        // Update link form checkboxes
        const linkEnvCheckboxes = document.getElementById('link-environment-checkboxes');
        if (linkEnvCheckboxes) {
            if (envs.length === 0) {
                linkEnvCheckboxes.innerHTML = '<p style="color: var(--text-secondary); text-align: center; margin: 0;">No environments available. Create one first!</p>';
            } else {
                linkEnvCheckboxes.innerHTML = envs.map(e => `
                    <label style="display: flex; align-items: center; gap: 10px; padding: 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;"
                           onmouseover="this.style.background='var(--primary-color)'; this.style.color='white';"
                           onmouseout="this.style.background='transparent'; this.style.color='inherit';">
                        <input type="checkbox" name="link-environment" value="${e.id}" style="width: 18px; height: 18px; cursor: pointer;">
                        <div style="width: 16px; height: 16px; border-radius: 4px; background: ${e.color};"></div>
                        <span style="flex: 1;">${e.name}</span>
                    </label>
                `).join('');
            }
        }
        
        // Display in env modal
        const envList = document.getElementById('env-list');
        if (envList) {
            envList.innerHTML = envs.map(e => `
                <div class="env-item" style="padding: 10px; background: var(--hover-bg); border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 20px; height: 20px; border-radius: 4px; background: ${e.color};"></div>
                        <span>${e.name}</span>
                    </div>
                    <button class="btn btn-danger btn-sm" onclick="deleteEnvironment(${e.id})">Delete</button>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading environments:', error);
    }
}

// Edit link
async function editLink(linkId) {
    try {
        const link = allLinks.find(l => l.id === linkId);
        if (!link) return;
        
        // Fill form with link data
        document.getElementById('link-name').value = link.name;
        document.getElementById('link-url').value = link.url;
        document.getElementById('link-description').value = link.description || '';
        
        // Check the appropriate environment checkbox
        const checkboxes = document.querySelectorAll('input[name="link-environment"]');
        checkboxes.forEach(cb => {
            cb.checked = (cb.value == link.environment_id);
        });
        
        // Update form mode
        isEditMode = true;
        currentLinkId = linkId;
        
        // Update modal title and button
        const modalTitle = document.querySelector('#link-modal .modal-header h2');
        if (modalTitle) {
            modalTitle.innerHTML = '<i class="fas fa-edit"></i> Edit Link';
        }
        
        const submitBtn = document.querySelector('#link-form button[type="submit"]');
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fas fa-save"></i> Update Link';
        }
        
        openModal('link-modal');
    } catch (error) {
        console.error('Error loading link:', error);
        showNotification('Failed to load link', 'error');
    }
}

// Reset link form
function resetLinkForm() {
    isEditMode = false;
    currentLinkId = null;
    document.getElementById('link-form').reset();
    
    // Uncheck all environment checkboxes
    const checkboxes = document.querySelectorAll('input[name="link-environment"]');
    checkboxes.forEach(cb => cb.checked = false);
    
    const modalTitle = document.querySelector('#link-modal .modal-header h2');
    if (modalTitle) {
        modalTitle.innerHTML = '<i class="fas fa-link"></i> Add New Link';
    }
    
    const submitBtn = document.querySelector('#link-form button[type="submit"]');
    if (submitBtn) {
        submitBtn.innerHTML = '<i class="fas fa-plus"></i> Add Link';
    }
}

async function handleLinkSubmit(e) {
    e.preventDefault();
    
    // Get all selected environments
    const checkedEnvs = Array.from(document.querySelectorAll('input[name="link-environment"]:checked'))
        .map(cb => parseInt(cb.value));
    
    const data = {
        name: document.getElementById('link-name').value,
        url: document.getElementById('link-url').value,
        description: document.getElementById('link-description').value,
        environment_id: checkedEnvs.length > 0 ? checkedEnvs[0] : null, // For now, use first selected
        environment_ids: checkedEnvs // Send all selected for future use
    };
    
    try {
        const url = isEditMode ? `/api/links/${currentLinkId}` : '/api/links';
        const method = isEditMode ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showNotification(isEditMode ? 'Link updated' : 'Link created', 'success');
            closeModal('link-modal');
            loadLinks();
            resetLinkForm();
        }
    } catch (error) {
        console.error('Error saving link:', error);
        showNotification('Failed to save link', 'error');
    }
}

async function handleEnvSubmit(e) {
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
            showNotification('Environment created', 'success');
            loadEnvironments();
            e.target.reset();
        }
    } catch (error) {
        console.error('Error creating environment:', error);
        showNotification('Failed to create environment', 'error');
    }
}

async function deleteLink(id) {
    if (!confirm('Delete this link?')) return;
    
    try {
        const response = await fetch(`/api/links/${id}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Link deleted', 'success');
            loadLinks();
        }
    } catch (error) {
        console.error('Error deleting link:', error);
    }
}

async function deleteEnvironment(id) {
    if (!confirm('Delete this environment?')) return;
    
    try {
        const response = await fetch(`/api/environments/${id}`, { method: 'DELETE' });
        if (response.ok) {
            showNotification('Environment deleted', 'success');
            loadEnvironments();
            loadLinks();
        }
    } catch (error) {
        console.error('Error deleting environment:', error);
    }
}

function showManageEnvModal() {
    openModal('env-modal');
}


function showManageEnvModal() {
    openModal('env-modal');
}

// Override modal close to reset form
document.addEventListener('DOMContentLoaded', function() {
    const linkModal = document.getElementById('link-modal');
    if (linkModal) {
        linkModal.addEventListener('click', function(e) {
            if (e.target === linkModal || e.target.classList.contains('close-btn')) {
                resetLinkForm();
            }
        });
    }
});

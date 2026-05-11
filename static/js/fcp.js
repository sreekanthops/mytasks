// FCP Manager JavaScript

// Load DCs on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDCs();
    loadHistory();
});

// Load available DCs
async function loadDCs() {
    try {
        const response = await fetch('/api/fcp/dcs');
        const dcs = await response.json();
        
        const dcGrid = document.getElementById('dc-grid');
        dcGrid.innerHTML = '';
        
        dcs.forEach(dc => {
            const dcCard = document.createElement('div');
            dcCard.className = 'dc-card';
            dcCard.innerHTML = `
                <h4>${dc.name}</h4>
                <p class="dc-id">${dc.id}</p>
                <small>${dc.full}</small>
            `;
            dcGrid.appendChild(dcCard);
        });
    } catch (error) {
        console.error('Error loading DCs:', error);
        document.getElementById('dc-grid').innerHTML = '<p class="error">Failed to load DCs</p>';
    }
}

// Load execution history
async function loadHistory() {
    try {
        const response = await fetch('/api/fcp/history');
        const history = await response.json();
        
        const historyList = document.getElementById('history-list');
        
        if (history.length === 0) {
            historyList.innerHTML = '<p class="loading">No execution history found</p>';
            return;
        }
        
        historyList.innerHTML = '';
        
        history.forEach((item, index) => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.innerHTML = `
                <div class="history-info">
                    <h4>${item.service}</h4>
                    <p>${item.trigger_name}</p>
                    <small>Toolchain: ${item.toolchain_name}</small>
                </div>
                <div class="history-actions">
                    <button class="btn btn-sm btn-primary" onclick="rerunFromHistory(${index + 1})">
                        <i class="fas fa-redo"></i> Re-run
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="openTerminalWithHistory(${index + 1})">
                        <i class="fas fa-terminal"></i> Terminal
                    </button>
                </div>
            `;
            historyList.appendChild(historyItem);
        });
    } catch (error) {
        console.error('Error loading history:', error);
        document.getElementById('history-list').innerHTML = '<p class="error">Failed to load history</p>';
    }
}

// Show trigger modal
function showTriggerModal() {
    document.getElementById('triggerModal').style.display = 'block';
    document.getElementById('triggerOutput').style.display = 'none';
    document.getElementById('triggerForm').reset();
}

// Close trigger modal
function closeTriggerModal() {
    document.getElementById('triggerModal').style.display = 'none';
}

// Show create trigger modal
function showCreateTriggerModal() {
    document.getElementById('createTriggerModal').style.display = 'block';
    document.getElementById('createTriggerOutput').style.display = 'none';
    document.getElementById('createTriggerForm').reset();
}

// Close create trigger modal
function closeCreateTriggerModal() {
    document.getElementById('createTriggerModal').style.display = 'none';
}

// Handle trigger form submission
document.getElementById('triggerForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const serviceName = document.getElementById('serviceName').value;
    const openInTerminal = document.getElementById('openTerminal').checked;
    
    if (openInTerminal) {
        // Open in terminal for interactive mode
        openTerminalWithService(serviceName);
        closeTriggerModal();
    } else {
        // Execute via API (non-interactive)
        await triggerPipeline(serviceName);
    }
});

// Handle create trigger form submission
document.getElementById('createTriggerForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const serviceName = document.getElementById('createServiceName').value;
    const dcSelection = document.getElementById('dcSelection');
    const selectedOptions = Array.from(dcSelection.selectedOptions).map(opt => opt.value);
    const openInTerminal = document.getElementById('openCreateTerminal').checked;
    
    if (selectedOptions.length === 0) {
        showNotification('Please select at least one DC', 'warning');
        return;
    }
    
    // Convert selections to DC input format
    let dcInput;
    if (selectedOptions.includes('all')) {
        dcInput = 'all';
    } else {
        dcInput = selectedOptions.join(',');
    }
    
    if (openInTerminal) {
        // Open in terminal for interactive mode (recommended)
        openTerminalForCreateTrigger(serviceName, dcInput);
        closeCreateTriggerModal();
    } else {
        // Execute via API (non-interactive)
        await createTrigger(serviceName, dcInput);
    }
});

// Trigger pipeline via API
async function triggerPipeline(serviceName) {
    const outputSection = document.getElementById('triggerOutput');
    const outputContent = document.getElementById('outputContent');
    
    outputSection.style.display = 'block';
    outputContent.textContent = 'Triggering pipeline...\n';
    
    try {
        const response = await fetch('/api/fcp/trigger', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                service_name: serviceName,
                mode: '1'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            outputContent.textContent = result.output;
            showNotification('Pipeline triggered successfully!', 'success');
            // Reload history after successful trigger
            setTimeout(loadHistory, 2000);
        } else {
            outputContent.textContent = `Error: ${result.error}\n\n${result.output || ''}`;
            showNotification('Failed to trigger pipeline', 'error');
        }
    } catch (error) {
        outputContent.textContent = `Error: ${error.message}`;
        showNotification('Failed to trigger pipeline', 'error');
    }
}

// Open terminal with service name
function openTerminalWithService(serviceName) {
    const scriptPath = '/Users/sreekanthchityala/nettools/internal-scripts/fcp/fcp_manager.sh';
    const command = `bash ${scriptPath} ${serviceName}`;
    
    // Try to open in Terminal.app (macOS)
    const terminalCommand = `osascript -e 'tell application "Terminal" to do script "cd ~ && ${command}"'`;
    
    // Show notification
    showNotification(`Opening terminal with service: ${serviceName}`, 'info');
    
    // Execute command to open terminal
    fetch('/api/fcp/trigger', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            service_name: serviceName,
            mode: 'terminal'
        })
    }).catch(error => {
        console.error('Error opening terminal:', error);
        showNotification('Please run manually: ' + command, 'warning');
    });
}

// Open terminal
function openTerminal() {
    const scriptPath = '/Users/sreekanthchityala/nettools/internal-scripts/fcp/fcp_manager.sh';
    showNotification('Opening FCP Manager in terminal...', 'info');
    
    // For macOS, open Terminal.app
    const command = `osascript -e 'tell application "Terminal" to do script "cd ~ && bash ${scriptPath}"'`;
    
    // Show instructions
    alert(`Opening FCP Manager in terminal.\n\nIf it doesn't open automatically, run:\nbash ${scriptPath}`);
}

// Re-run from history
function rerunFromHistory(historyNumber) {
    const scriptPath = '/Users/sreekanthchityala/nettools/internal-scripts/fcp/fcp_manager.sh';
    const command = `bash ${scriptPath} ${historyNumber}`;
    
    showNotification(`Re-running history entry #${historyNumber}`, 'info');
    
    // Open in terminal
    const terminalCommand = `osascript -e 'tell application "Terminal" to do script "cd ~ && ${command}"'`;
    
    alert(`Re-running history entry #${historyNumber}\n\nCommand: ${command}`);
}

// Open terminal with history number
function openTerminalWithHistory(historyNumber) {
    const scriptPath = '/Users/sreekanthchityala/nettools/internal-scripts/fcp/fcp_manager.sh';
    const command = `bash ${scriptPath} ${historyNumber}`;
    
    showNotification(`Opening terminal with history #${historyNumber}`, 'info');
    alert(`Opening terminal with history entry #${historyNumber}\n\nCommand: ${command}`);
}

// Open terminal for create trigger
function openTerminalForCreateTrigger(serviceName, dcInput) {
    const scriptPath = '/Users/sreekanthchityala/nettools/internal-scripts/fcp/fcp_manager.sh';
    
    showNotification(`Opening FCP Manager to create trigger for ${serviceName}`, 'info');
    
    // Instructions for the user
    const instructions = `
Opening FCP Manager in terminal...

Steps:
1. Select option 2 (Create New Trigger)
2. Enter service name: ${serviceName}
3. Select DC(s): ${dcInput}
4. Follow the prompts to complete trigger creation

If terminal doesn't open automatically, run:
bash ${scriptPath}
    `.trim();
    
    alert(instructions);
    
    // Try to open terminal (macOS)
    const terminalCommand = `osascript -e 'tell application "Terminal" to do script "cd ~ && bash ${scriptPath}"'`;
    
    // Note: The actual terminal opening would need backend support
    // For now, we show instructions
}

// Create trigger via API (non-interactive)
async function createTrigger(serviceName, dcInput) {
    const outputSection = document.getElementById('createTriggerOutput');
    const outputContent = document.getElementById('createOutputContent');
    
    outputSection.style.display = 'block';
    outputContent.textContent = 'Creating trigger...\n';
    
    try {
        const response = await fetch('/api/fcp/trigger', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                service_name: serviceName,
                mode: '2',
                dc_selection: dcInput
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            outputContent.textContent = result.output;
            showNotification('Trigger created successfully!', 'success');
            // Reload history after successful creation
            setTimeout(loadHistory, 2000);
        } else {
            outputContent.textContent = `Error: ${result.error}\n\n${result.output || ''}`;
            showNotification('Failed to create trigger', 'error');
        }
    } catch (error) {
        outputContent.textContent = `Error: ${error.message}`;
        showNotification('Failed to create trigger', 'error');
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Close modal when clicking outside
window.onclick = function(event) {
    const triggerModal = document.getElementById('triggerModal');
    const createTriggerModal = document.getElementById('createTriggerModal');
    
    if (event.target === triggerModal) {
        closeTriggerModal();
    } else if (event.target === createTriggerModal) {
        closeCreateTriggerModal();
    }
};

// Made with Bob

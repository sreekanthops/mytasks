// FCP Manager Wizard JavaScript
let currentStep = 1;
let wizardData = {
    mode: null,
    serviceName: null,
    toolchain: null,
    trigger: null,
    dcs: [],
    config: {},
    envFilter: 'all',  // all, ngdc, fcp
    typeFilter: 'deploy'  // deploy, promotion
};

// Initialize wizard
document.addEventListener('DOMContentLoaded', function() {
    console.log('FCP Wizard initialized');
});

// Mode selection
function selectMode(mode) {
    wizardData.mode = mode;
    console.log('Mode selected:', mode);
    nextStep();
}

// Navigation functions
function nextStep() {
    if (currentStep < 5) {
        // Hide current step
        document.getElementById(`step-${currentStep}`).classList.remove('active');
        document.querySelector(`.wizard-progress .step[data-step="${currentStep}"]`).classList.add('completed');
        
        // Show next step
        currentStep++;
        document.getElementById(`step-${currentStep}`).classList.add('active');
        document.querySelector(`.wizard-progress .step[data-step="${currentStep}"]`).classList.add('active');
        
        // Load step content
        loadStepContent();
    }
}

function previousStep() {
    if (currentStep > 1) {
        // Hide current step
        document.getElementById(`step-${currentStep}`).classList.remove('active');
        document.querySelector(`.wizard-progress .step[data-step="${currentStep}"]`).classList.remove('active');
        
        // Show previous step
        currentStep--;
        document.getElementById(`step-${currentStep}`).classList.add('active');
        document.querySelector(`.wizard-progress .step[data-step="${currentStep}"]`).classList.remove('completed');
    }
}

function resetWizard() {
    currentStep = 1;
    wizardData = {
        mode: null,
        serviceName: null,
        toolchain: null,
        trigger: null,
        dcs: [],
        config: {}
    };
    
    // Reset all steps
    document.querySelectorAll('.wizard-step').forEach(step => step.classList.remove('active'));
    document.querySelectorAll('.wizard-progress .step').forEach(step => {
        step.classList.remove('active', 'completed');
    });
    
    // Show first step
    document.getElementById('step-1').classList.add('active');
    document.querySelector('.wizard-progress .step[data-step="1"]').classList.add('active');
}

// Search for service
async function searchService() {
    const serviceName = document.getElementById('serviceName').value.trim();
    
    if (!serviceName) {
        showValidation('Please enter a service name', 'error');
        return;
    }
    
    wizardData.serviceName = serviceName;
    showValidation('Searching for toolchains...', 'success');
    
    try {
        const response = await fetch('/api/fcp/search-toolchains', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ service_name: serviceName })
        });
        
        const result = await response.json();
        
        if (result.success && result.toolchains && result.toolchains.length > 0) {
            wizardData.toolchains = result.toolchains;
            showValidation(`Found ${result.toolchains.length} toolchain(s)`, 'success');
            setTimeout(nextStep, 500);
        } else {
            showValidation('No toolchains found for this service', 'error');
        }
    } catch (error) {
        console.error('Error searching toolchains:', error);
        showValidation('Error searching for toolchains. Please try again.', 'error');
    }
}

function showValidation(message, type) {
    const validationDiv = document.getElementById('serviceValidation');
    validationDiv.textContent = message;
    validationDiv.className = `validation-message ${type}`;
}

// Load step content dynamically
function loadStepContent() {
    if (currentStep === 3) {
        loadStep3Content();
    } else if (currentStep === 4) {
        loadStep4Content();
    }
}

// Load Step 3 content (Toolchain/Trigger/DC selection)
function loadStep3Content() {
    const content = document.getElementById('selectionContent');
    const title = document.getElementById('step3Title');
    const description = document.getElementById('step3Description');
    
    // Check if we need to show toolchain selection first
    if (!wizardData.toolchain && wizardData.toolchains && wizardData.toolchains.length > 1) {
        // Show toolchain selection for both modes when multiple toolchains exist
        title.textContent = 'Select Toolchain';
        description.textContent = `Found ${wizardData.toolchains.length} toolchains. Choose one to continue.`;
        
        let html = '<div class="selection-grid">';
        wizardData.toolchains.forEach((tc, index) => {
            html += `
                <div class="selection-item" onclick="selectToolchain(${index})">
                    <h4>${tc.name}</h4>
                    <p><small>${tc.toolchain_guid}</small></p>
                </div>
            `;
        });
        html += '</div>';
        content.innerHTML = html;
        return;
    }
    
    // Auto-select toolchain if only one
    if (!wizardData.toolchain && wizardData.toolchains && wizardData.toolchains.length === 1) {
        wizardData.toolchain = wizardData.toolchains[0];
    }
    
    if (wizardData.mode === 'trigger') {
        // Show trigger selection for trigger mode
        title.textContent = 'Select Trigger';
        description.textContent = 'Choose the manual CD trigger to execute';
        
        if (!wizardData.triggers || wizardData.triggers.length === 0) {
            content.innerHTML = '<p class="text-muted">Loading triggers...</p>';
            return;
        }
        
        let html = '<div class="selection-grid">';
        wizardData.triggers.forEach((trigger, index) => {
            html += `
                <div class="selection-item" onclick="selectTrigger(${index})">
                    <h4>${trigger.name}</h4>
                    <p><small>${trigger.id}</small></p>
                </div>
            `;
        });
        html += '</div>';
        content.innerHTML = html;
        
    } else if (wizardData.mode === 'create') {
        // Show DC selection for create mode
        title.textContent = 'Select Data Centers';
        description.textContent = 'Choose one or more DCs to create triggers for';
        
        const dcs = [
            { id: 'syd05', name: 'Sydney 05', full: 'syd0501' },
            { id: 'lon02', name: 'London 02', full: 'lon0201' },
            { id: 'lon05', name: 'London 05', full: 'lon0501' },
            { id: 'lon06', name: 'London 06', full: 'lon0601' },
            { id: 'osa23', name: 'Osaka 23', full: 'osa2301' },
            { id: 'syd04', name: 'Sydney 04', full: 'syd0401' }
        ];
        
        let html = '<div class="selection-grid">';
        dcs.forEach(dc => {
            html += `
                <div class="selection-item" onclick="toggleDC('${dc.id}')">
                    <h4>${dc.name}</h4>
                    <p>${dc.id}</p>
                    <small>${dc.full}</small>
                </div>
            `;
        });
        html += '</div>';
        html += '<button class="btn btn-secondary" onclick="selectAllDCs()">Select All DCs</button>';
        content.innerHTML = html;
    }
}

// Select toolchain
async function selectToolchain(index) {
    wizardData.toolchain = wizardData.toolchains[index];
    
    // Highlight selected
    document.querySelectorAll('.selection-item').forEach(item => item.classList.remove('selected'));
    event.target.closest('.selection-item').classList.add('selected');
    
    addLog(`Selected toolchain: ${wizardData.toolchain.name}`);
    
    if (wizardData.mode === 'trigger') {
        // Load triggers for this toolchain
        addLog(`Loading triggers for ${wizardData.toolchain.name}...`);
        
        try {
            const response = await fetch('/api/fcp/get-triggers', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    toolchain_guid: wizardData.toolchain.toolchain_guid
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.triggers) {
                wizardData.triggers = result.triggers;
                showTriggerSelection();
            }
        } catch (error) {
            console.error('Error loading triggers:', error);
        }
    } else if (wizardData.mode === 'create') {
        // For create mode, reload step 3 to show DC selection
        loadStep3Content();
    }
}

// Show trigger selection with filters
function showTriggerSelection() {
    const content = document.getElementById('selectionContent');
    const title = document.getElementById('step3Title');
    const description = document.getElementById('step3Description');
    
    title.textContent = 'Select Trigger';
    description.textContent = 'Choose the trigger to execute';
    
    // Filter buttons HTML
    let html = `
        <div class="filter-section">
            <div class="filter-group">
                <label>Environment:</label>
                <div class="btn-group">
                    <button class="btn btn-sm ${wizardData.envFilter === 'all' ? 'btn-primary' : 'btn-outline-primary'}"
                            onclick="setEnvFilter('all')">All</button>
                    <button class="btn btn-sm ${wizardData.envFilter === 'ngdc' ? 'btn-primary' : 'btn-outline-primary'}"
                            onclick="setEnvFilter('ngdc')">NGDC</button>
                    <button class="btn btn-sm ${wizardData.envFilter === 'fcp' ? 'btn-primary' : 'btn-outline-primary'}"
                            onclick="setEnvFilter('fcp')">FCP</button>
                </div>
            </div>
            <div class="filter-group">
                <label>Trigger Type:</label>
                <div class="btn-group">
                    <button class="btn btn-sm ${wizardData.typeFilter === 'deploy' ? 'btn-success' : 'btn-outline-success'}"
                            onclick="setTypeFilter('deploy')">Deploy</button>
                    <button class="btn btn-sm ${wizardData.typeFilter === 'promotion' ? 'btn-success' : 'btn-outline-success'}"
                            onclick="setTypeFilter('promotion')">Promotion</button>
                </div>
            </div>
        </div>
    `;
    
    // Filter triggers based on selected filters
    const filteredTriggers = wizardData.triggers.filter(trigger => {
        const name = trigger.name.toLowerCase();
        
        // Environment filter
        let envMatch = true;
        if (wizardData.envFilter === 'ngdc') {
            envMatch = !name.includes('fcp');
        } else if (wizardData.envFilter === 'fcp') {
            envMatch = name.includes('fcp');
        }
        
        // Type filter
        let typeMatch = true;
        if (wizardData.typeFilter === 'promotion') {
            typeMatch = name.includes('promotion');
        } else if (wizardData.typeFilter === 'deploy') {
            typeMatch = trigger.type === 'manual' && !name.includes('promotion');
        }
        
        return envMatch && typeMatch;
    });
    
    // Display filtered triggers
    html += '<div class="selection-grid">';
    if (filteredTriggers.length === 0) {
        html += '<p class="text-muted">No triggers found matching the selected filters</p>';
    } else {
        filteredTriggers.forEach((trigger, index) => {
            // Find original index
            const originalIndex = wizardData.triggers.indexOf(trigger);
            html += `
                <div class="selection-item" onclick="selectTrigger(${originalIndex})">
                    <h4>${trigger.name}</h4>
                    <p><small>${trigger.type}</small></p>
                </div>
            `;
        });
    }
    html += '</div>';
    
    content.innerHTML = html;
}

// Set environment filter
function setEnvFilter(filter) {
    wizardData.envFilter = filter;
    showTriggerSelection();
}

// Set type filter
function setTypeFilter(filter) {
    wizardData.typeFilter = filter;
    showTriggerSelection();
}

// Select trigger
function selectTrigger(index) {
    wizardData.trigger = wizardData.triggers[index];
    
    // Highlight selected
    document.querySelectorAll('.selection-item').forEach(item => item.classList.remove('selected'));
    event.target.closest('.selection-item').classList.add('selected');
    
    // Enable next button
    document.getElementById('step3NextBtn').disabled = false;
}

// Toggle DC selection
function toggleDC(dcId) {
    const index = wizardData.dcs.indexOf(dcId);
    const item = event.target.closest('.selection-item');
    
    if (index > -1) {
        wizardData.dcs.splice(index, 1);
        item.classList.remove('selected');
    } else {
        wizardData.dcs.push(dcId);
        item.classList.add('selected');
    }
    
    // Enable next button if at least one DC selected
    document.getElementById('step3NextBtn').disabled = wizardData.dcs.length === 0;
}

// Select all DCs
function selectAllDCs() {
    const dcs = ['syd05', 'lon02', 'lon05', 'lon06', 'osa23', 'syd04'];
    wizardData.dcs = [...dcs];
    
    document.querySelectorAll('.selection-item').forEach(item => {
        item.classList.add('selected');
    });
    
    document.getElementById('step3NextBtn').disabled = false;
}

// Load Step 4 content (Configuration)
async function loadStep4Content() {
    const content = document.getElementById('configContent');
    const title = document.getElementById('step4Title');
    const description = document.getElementById('step4Description');
    const executeBtn = document.getElementById('executeBtn');
    
    if (wizardData.mode === 'trigger') {
        title.textContent = 'Review & Edit Parameters';
        description.textContent = 'Review and modify trigger parameters before execution';
        
        // Show loading state
        content.innerHTML = '<p class="text-muted"><i class="fas fa-spinner fa-spin"></i> Loading trigger properties...</p>';
        
        try {
            // Fetch trigger properties
            const response = await fetch('/api/fcp/get-trigger-properties', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    toolchain_guid: wizardData.toolchain.toolchain_guid,
                    trigger_id: wizardData.trigger.id
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.properties) {
                wizardData.properties = result.properties;
                wizardData.propertyOverrides = {};
                
                let html = '<div class="config-section">';
                html += '<h3>Trigger Details</h3>';
                html += `
                    <div class="config-item">
                        <span class="config-label">Service:</span>
                        <span class="config-value">${wizardData.serviceName}</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">Toolchain:</span>
                        <span class="config-value">${wizardData.toolchain.name}</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">Trigger:</span>
                        <span class="config-value">${wizardData.trigger.name}</span>
                    </div>
                `;
                html += '</div>';
                
                // Add parameters section
                html += '<div class="config-section" style="margin-top: 2rem;">';
                html += '<h3>Pipeline Parameters <small style="color: #666;">(Click to edit)</small></h3>';
                html += '<div class="params-grid">';
                
                result.properties.forEach((prop, index) => {
                    const isSecure = prop.type === 'secure' || prop.type === 'integration';
                    const displayValue = isSecure ? '••••••••' : (prop.value || '');
                    
                    html += `
                        <div class="param-item" data-index="${index}">
                            <div class="param-header">
                                <span class="param-name">${prop.name}</span>
                                <span class="param-type">${prop.type}</span>
                            </div>
                            <div class="param-value-container">
                                <input type="${isSecure ? 'password' : 'text'}"
                                       class="param-input"
                                       id="param-${index}"
                                       value="${displayValue}"
                                       ${isSecure ? 'readonly' : ''}
                                       onchange="updateProperty(${index}, this.value)"
                                       placeholder="${prop.name}">
                                ${!isSecure ? '<button class="btn-edit" onclick="focusParam(' + index + ')"><i class="fas fa-edit"></i></button>' : ''}
                            </div>
                        </div>
                    `;
                });
                
                html += '</div></div>';
                content.innerHTML = html;
                
                // Show execute button
                executeBtn.style.display = 'inline-block';
                executeBtn.innerHTML = '<i class="fas fa-rocket"></i> Execute';
            } else {
                content.innerHTML = '<p class="text-danger">Failed to load trigger properties</p>';
            }
        } catch (error) {
            console.error('Error loading properties:', error);
            content.innerHTML = '<p class="text-danger">Error loading trigger properties</p>';
        }
        
    } else if (wizardData.mode === 'create') {
        title.textContent = 'Review Configuration';
        description.textContent = 'Review the configuration - execution will open in terminal for best performance';
        
        let html = '<div class="config-section">';
        html += '<h3>Trigger Creation Details</h3>';
        html += `
            <div class="config-item">
                <span class="config-label">Service:</span>
                <span class="config-value">${wizardData.serviceName}</span>
            </div>
            <div class="config-item">
                <span class="config-label">Toolchain:</span>
                <span class="config-value">${wizardData.toolchain ? wizardData.toolchain.name : 'Auto-detected'}</span>
            </div>
            <div class="config-item">
                <span class="config-label">Data Centers:</span>
                <span class="config-value">${wizardData.dcs.join(', ')}</span>
            </div>
            <div class="config-item">
                <span class="config-label">Number of Triggers:</span>
                <span class="config-value">${wizardData.dcs.length}</span>
            </div>
        `;
        html += '</div>';
        
        // Add info box about terminal execution
        html += `
            <div class="alert alert-info" style="margin-top: 1.5rem;">
                <i class="fas fa-info-circle"></i>
                <div>
                    <strong>Terminal Execution</strong>
                    <p>For best performance, trigger creation will open in your terminal.
                    The FCP Manager script will guide you through the process interactively.</p>
                </div>
            </div>
        `;
        
        content.innerHTML = html;
        
        // Show execute button normally for create mode too
        executeBtn.style.display = 'inline-block';
        executeBtn.innerHTML = '<i class="fas fa-play"></i> Create Triggers';
    }
}

// Update property value
function updateProperty(index, value) {
    const prop = wizardData.properties[index];
    if (!wizardData.propertyOverrides) {
        wizardData.propertyOverrides = {};
    }
    wizardData.propertyOverrides[prop.name] = value;
    console.log('Property updated:', prop.name, '=', value);
}

// Focus on parameter input
function focusParam(index) {
    const input = document.getElementById(`param-${index}`);
    if (input) {
        input.focus();
        input.select();
    }
}

// Execute action
async function executeAction() {
    // Move to execution step
    nextStep();
    
    if (wizardData.mode === 'trigger') {
        await executeTrigger();
    } else if (wizardData.mode === 'create') {
        await createTriggers();
    }
}

// Execute trigger
async function executeTrigger() {
    updateStatus('Triggering pipeline...');
    addLog('Starting pipeline execution...');
    addLog(`Service: ${wizardData.serviceName}`);
    addLog(`Trigger: ${wizardData.trigger.name}`);
    
    // Log property overrides if any
    if (wizardData.propertyOverrides && Object.keys(wizardData.propertyOverrides).length > 0) {
        addLog('Modified parameters:');
        Object.entries(wizardData.propertyOverrides).forEach(([key, value]) => {
            addLog(`  ${key}: ${value}`);
        });
    }
    
    try {
        const response = await fetch('/api/fcp/trigger-pipeline', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                toolchain_guid: wizardData.toolchain.toolchain_guid,
                trigger_id: wizardData.trigger.id,
                properties: wizardData.propertyOverrides || {}
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            addLog('✓ Pipeline triggered successfully!', 'success');
            addLog(`Run ID: ${result.run_id || 'N/A'}`);
            if (result.url) {
                addLog(`URL: ${result.url}`);
            }
            updateStatus('Execution completed successfully!');
            showDoneButton();
        } else {
            addLog(`✗ Error: ${result.error}`, 'error');
            updateStatus('Execution failed');
        }
    } catch (error) {
        console.error('Execution error:', error);
        addLog(`✗ Error: ${error.message}`, 'error');
        updateStatus('Execution failed');
    }
}

// Create triggers
async function createTriggers() {
    updateStatus('Creating triggers...');
    addLog('Starting trigger creation...');
    addLog(`Service: ${wizardData.serviceName}`);
    addLog(`Toolchain: ${wizardData.toolchain.name}`);
    addLog(`DCs: ${wizardData.dcs.join(', ')}`);
    addLog('');
    
    let successCount = 0;
    let failCount = 0;
    
    for (const dc of wizardData.dcs) {
        addLog(`Processing DC: ${dc}...`);
        
        try {
            const response = await fetch('/api/fcp/create-trigger', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    service_name: wizardData.serviceName,
                    dc: dc,
                    toolchain_guid: wizardData.toolchain.toolchain_guid
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                addLog(`✓ ${result.message || 'Trigger created for ' + dc}`, 'success');
                if (result.trigger_id) {
                    addLog(`  Trigger ID: ${result.trigger_id}`);
                }
                successCount++;
            } else {
                addLog(`✗ Failed for ${dc}: ${result.error}`, 'error');
                if (result.traceback) {
                    console.error('Traceback:', result.traceback);
                }
                failCount++;
            }
        } catch (error) {
            console.error(`Error for ${dc}:`, error);
            addLog(`✗ Error for ${dc}: ${error.message}`, 'error');
            failCount++;
        }
        
        addLog('');
    }
    
    addLog('=== Summary ===');
    addLog(`✓ Successful: ${successCount}`, 'success');
    if (failCount > 0) {
        addLog(`✗ Failed: ${failCount}`, 'error');
    }
    
    updateStatus(`Completed: ${successCount} successful, ${failCount} failed`);
    showDoneButton();
}

// Helper functions
function updateStatus(text) {
    document.getElementById('statusText').textContent = text;
}

function addLog(message, type = 'info') {
    const logContent = document.getElementById('logContent');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logContent.appendChild(entry);
    logContent.scrollTop = logContent.scrollHeight;
}

function clearLogs() {
    document.getElementById('logContent').innerHTML = '';
}

function showDoneButton() {
    document.getElementById('doneBtn').style.display = 'inline-block';
    document.querySelector('.status-indicator i').className = 'fas fa-check-circle';
}

// Made with Bob

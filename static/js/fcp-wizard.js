// Pipelines Wizard JavaScript
let currentStep = 1;
let wizardData = {
    mode: null,
    pipelineType: null,  // 'ci' or 'cd'
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
    console.log('Pipelines Wizard initialized');
});

// Mode selection
function selectMode(mode) {
    wizardData.mode = mode;
    console.log('Mode selected:', mode);
    
    if (mode === 'trigger') {
        // Show pipeline type selection (step 1.5)
        document.getElementById('step-1').classList.remove('active');
        document.getElementById('step-1-5').classList.add('active');
    } else {
        // For 'create' mode, go directly to step 2
        nextStep();
    }
}

// Pipeline type selection
function selectPipelineType(type) {
    wizardData.pipelineType = type;
    console.log('Pipeline type selected:', type);
    
    // Hide step 1.5 and move to step 2
    document.getElementById('step-1-5').classList.remove('active');
    document.querySelector('.wizard-progress .step[data-step="1"]').classList.add('completed');
    
    currentStep = 2;
    document.getElementById('step-2').classList.add('active');
    document.querySelector('.wizard-progress .step[data-step="2"]').classList.add('active');
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
        pipelineType: null,
        serviceName: null,
        toolchain: null,
        trigger: null,
        dcs: [],
        customDCs: [],
        config: {},
        envFilter: 'all',
        typeFilter: 'deploy'
    };
    
    // Reset all steps
    document.querySelectorAll('.wizard-step').forEach(step => step.classList.remove('active'));
    document.querySelectorAll('.wizard-progress .step').forEach(step => {
        step.classList.remove('active', 'completed');
    });
    
    // Show first step
    document.getElementById('step-1').classList.add('active');
    document.querySelector('.wizard-progress .step[data-step="1"]').classList.add('active');
    
    // Clear any logs
    const logContent = document.getElementById('logContent');
    if (logContent) {
        logContent.innerHTML = '<div class="log-entry">Waiting for execution to start...</div>';
    }
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
            body: JSON.stringify({
                service_name: serviceName,
                pipeline_type: wizardData.pipelineType
            })
        });
        
        const result = await response.json();
        console.log('Search result:', result);
        
        if (result.success && result.toolchains && result.toolchains.length > 0) {
            wizardData.toolchains = result.toolchains;
            console.log('Toolchains stored:', wizardData.toolchains);
            showValidation(`Found ${result.toolchains.length} toolchain(s)`, 'success');
            setTimeout(nextStep, 500);
        } else {
            console.log('No toolchains found or invalid response');
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
    console.log('loadStep3Content called');
    console.log('wizardData:', wizardData);
    
    const content = document.getElementById('selectionContent');
    const title = document.getElementById('step3Title');
    const description = document.getElementById('step3Description');
    
    // Check if we need to show toolchain selection first
    if (!wizardData.toolchain && wizardData.toolchains && wizardData.toolchains.length > 1) {
        console.log('Showing toolchain selection for multiple toolchains');
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
    
    // Auto-select toolchain if only one and fetch triggers
    if (!wizardData.toolchain && wizardData.toolchains && wizardData.toolchains.length === 1) {
        console.log('Auto-selecting single toolchain');
        wizardData.toolchain = wizardData.toolchains[0];
        console.log('Selected toolchain:', wizardData.toolchain);
        // Fetch triggers for the auto-selected toolchain
        if (wizardData.mode === 'trigger') {
            console.log('Calling selectToolchain(0) for trigger mode');
            selectToolchain(0);
            return;
        }
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
        console.log('Showing DC selection for create mode');
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
        
        // Add custom DC option
        html += `
            <div class="selection-item" onclick="showCustomDCModal()" style="border: 2px dashed #6366f1; background: #f0f9ff;">
                <h4><i class="fas fa-plus-circle"></i> Add Custom DC</h4>
                <p>Enter custom DC code</p>
                <small>e.g., dal10, wdc04</small>
            </div>
        `;
        
        html += '</div>';
        
        // Show selected custom DCs if any
        if (wizardData.customDCs && wizardData.customDCs.length > 0) {
            html += '<div style="margin-top: 1rem; padding: 1rem; background: #f0f9ff; border-radius: 8px;">';
            html += '<strong>Custom DCs:</strong> ';
            wizardData.customDCs.forEach(dc => {
                html += `<span style="display: inline-block; margin: 0.25rem; padding: 0.5rem 1rem; background: #6366f1; color: white; border-radius: 6px;">${dc} <i class="fas fa-times" onclick="removeCustomDC('${dc}')" style="cursor: pointer; margin-left: 0.5rem;"></i></span>`;
            });
            html += '</div>';
        }
        
        html += '<div style="margin-top: 1rem;">';
        html += '<button class="btn btn-secondary" onclick="selectAllDCs()">Select All DCs</button>';
        html += '</div>';
        content.innerHTML = html;
    }
}

// Select toolchain
async function selectToolchain(index) {
    wizardData.toolchain = wizardData.toolchains[index];
    
    // Highlight selected (only if called from UI click)
    if (typeof event !== 'undefined' && event.target) {
        document.querySelectorAll('.selection-item').forEach(item => item.classList.remove('selected'));
        event.target.closest('.selection-item').classList.add('selected');
    }
    
    addLog(`Selected toolchain: ${wizardData.toolchain.name}`);
    
    if (wizardData.mode === 'trigger') {
        // Load triggers for this toolchain
        addLog(`Loading ${wizardData.pipelineType.toUpperCase()} triggers for ${wizardData.toolchain.name}...`);
        
        try {
            const response = await fetch('/api/fcp/get-triggers', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    toolchain_guid: wizardData.toolchain.toolchain_guid,
                    pipeline_type: wizardData.pipelineType
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
    
    // Filter buttons HTML - different filters for CI vs CD
    let html = '';
    
    if (wizardData.pipelineType === 'cd') {
        // CD pipeline filters
        html = `
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
    } else {
        // CI pipeline filters - simpler, just environment
        html = `
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
            </div>
        `;
    }
    
    // Filter triggers based on selected filters and pipeline type
    const filteredTriggers = wizardData.triggers.filter(trigger => {
        const name = trigger.name.toLowerCase();
        
        // Environment filter (applies to both CI and CD)
        let envMatch = true;
        if (wizardData.envFilter === 'ngdc') {
            envMatch = !name.includes('fcp');
        } else if (wizardData.envFilter === 'fcp') {
            envMatch = name.includes('fcp');
        }
        
        // Type filter (only for CD pipelines)
        let typeMatch = true;
        if (wizardData.pipelineType === 'cd') {
            if (wizardData.typeFilter === 'promotion') {
                typeMatch = name.includes('promotion');
            } else if (wizardData.typeFilter === 'deploy') {
                typeMatch = trigger.type === 'manual' && !name.includes('promotion');
            }
        }
        // For CI pipelines, all triggers pass the type filter
        
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
            // Get color based on DC name
            const dcColor = getDCColor(trigger.name);
            html += `
                <div class="selection-item" onclick="selectTrigger(${originalIndex})"
                     style="border-left: 4px solid ${dcColor};">
                    <h4>${trigger.name}</h4>
                    <p><small>${trigger.type}</small></p>
                    <div class="dc-indicator" style="position: absolute; top: 10px; right: 10px; width: 12px; height: 12px; border-radius: 50%; background: ${dcColor};"></div>
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

// Show custom DC modal
function showCustomDCModal() {
    const dcCode = prompt('Enter custom DC code (e.g., dal10, wdc04, fra02):');
    
    if (dcCode && dcCode.trim()) {
        const cleanDC = dcCode.trim().toLowerCase();
        
        // Initialize customDCs array if not exists
        if (!wizardData.customDCs) {
            wizardData.customDCs = [];
        }
        
        // Check if DC already added
        if (wizardData.customDCs.includes(cleanDC)) {
            alert(`DC "${cleanDC}" is already added!`);
            return;
        }
        
        // Add to custom DCs
        wizardData.customDCs.push(cleanDC);
        
        // Add to selected DCs
        if (!wizardData.dcs.includes(cleanDC)) {
            wizardData.dcs.push(cleanDC);
        }
        
        // Reload step 3 to show the new DC
        loadStep3Content();
        
        // Enable next button
        document.getElementById('step3NextBtn').disabled = false;
        
        console.log('Added custom DC:', cleanDC);
        console.log('Current DCs:', wizardData.dcs);
    }
}

// Remove custom DC
function removeCustomDC(dcCode) {
    if (!wizardData.customDCs) return;
    
    // Remove from custom DCs
    wizardData.customDCs = wizardData.customDCs.filter(dc => dc !== dcCode);
    
    // Remove from selected DCs
    wizardData.dcs = wizardData.dcs.filter(dc => dc !== dcCode);
    
    // Reload step 3
    loadStep3Content();
    
    // Update next button state
    document.getElementById('step3NextBtn').disabled = wizardData.dcs.length === 0;
    
    console.log('Removed custom DC:', dcCode);
    console.log('Current DCs:', wizardData.dcs);
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
                wizardData.globalProperties = result.global_properties || {};
                wizardData.propertyOverrides = {};
                
                // Auto-set FCP branch parameters if this is an FCP CD trigger
                const isFCP = wizardData.trigger.name.toLowerCase().includes('fcp');
                if (isFCP && wizardData.pipelineType === 'cd') {
                    wizardData.propertyOverrides['one-pipeline-config-branch'] = 'fcp-classic-pipeline';
                    wizardData.propertyOverrides['pipeline-config-branch'] = 'fcp-classic-pipeline';
                    console.log('FCP CD trigger detected - pre-setting both branches to fcp-classic-pipeline');
                }
                
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
                
                // Add parameters section with search
                html += '<div class="config-section" style="margin-top: 2rem;">';
                html += '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">';
                html += '<h3 style="margin: 0;">Pipeline Parameters <small style="color: #666;">(Click to edit)</small></h3>';
                html += `
                    <div style="position: relative; width: 300px;">
                        <input type="text"
                               id="paramSearch"
                               class="param-input"
                               placeholder="Search parameters..."
                               onkeyup="filterParameters()"
                               style="padding-left: 2.5rem;">
                        <i class="fas fa-search" style="position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); color: #666;"></i>
                    </div>
                `;
                html += '</div>';
                
                html += '<div class="params-grid" id="paramsGrid">';
                
                // Section 1: Trigger-specific parameters
                if (result.properties && result.properties.length > 0) {
                    html += '<div class="param-section-header" style="grid-column: 1/-1; padding: 0.5rem 0; border-bottom: 2px solid #e5e7eb; margin-bottom: 0.5rem;">';
                    html += '<strong style="color: #374151;">Trigger Parameters</strong>';
                    html += '</div>';
                    
                    result.properties.forEach((prop, index) => {
                        const isSecure = prop.type === 'secure' || prop.type === 'integration';
                        let displayValue;
                        if (isSecure) {
                            displayValue = '••••••••';
                        } else {
                            displayValue = wizardData.propertyOverrides[prop.name] || prop.value || '';
                        }
                        
                        html += `
                            <div class="param-item" data-param-name="${prop.name.toLowerCase()}" data-index="${index}">
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
                }
                
                // Section 2: Global/Pipeline parameters
                if (result.global_properties && Object.keys(result.global_properties).length > 0) {
                    html += '<div class="param-section-header" style="grid-column: 1/-1; padding: 0.5rem 0; border-bottom: 2px solid #e5e7eb; margin: 1rem 0 0.5rem 0;">';
                    html += '<strong style="color: #374151;">Global Pipeline Parameters</strong>';
                    html += '</div>';
                    
                    // For CD pipelines, show one-pipeline-config-branch first if it exists
                    if (wizardData.pipelineType === 'cd' && result.global_properties['one-pipeline-config-branch']) {
                        const onePipelineBranch = wizardData.propertyOverrides['one-pipeline-config-branch'] ||
                                                 result.global_properties['one-pipeline-config-branch'] ||
                                                 'fcp-classic-pipeline';
                        
                        html += `
                            <div class="param-item" data-param-name="one-pipeline-config-branch" data-index="global-one-pipeline-branch">
                                <div class="param-header">
                                    <span class="param-name">one-pipeline-config-branch</span>
                                    <span class="param-type" style="background: #0f62fe;">global</span>
                                </div>
                                <div class="param-value-container">
                                    <input type="text"
                                           class="param-input"
                                           id="param-global-one-pipeline-branch"
                                           value="${onePipelineBranch}"
                                           onchange="updateGlobalProperty('one-pipeline-config-branch', this.value)"
                                           placeholder="fcp-classic-pipeline">
                                    <button class="btn-edit" onclick="focusGlobalParam('global-one-pipeline-branch')"><i class="fas fa-edit"></i></button>
                                </div>
                            </div>
                        `;
                    }
                    
                    // Show all other global properties
                    Object.entries(result.global_properties).forEach(([name, value], index) => {
                        // Skip one-pipeline-config-branch if already shown for CD
                        if (wizardData.pipelineType === 'cd' && name === 'one-pipeline-config-branch') {
                            return;
                        }
                        
                        const displayValue = wizardData.propertyOverrides[name] || value || '';
                        const globalIndex = `global-${index}`;
                        
                        html += `
                            <div class="param-item" data-param-name="${name.toLowerCase()}" data-index="${globalIndex}">
                                <div class="param-header">
                                    <span class="param-name">${name}</span>
                                    <span class="param-type" style="background: #6b7280;">global</span>
                                </div>
                                <div class="param-value-container">
                                    <input type="text"
                                           class="param-input"
                                           id="param-${globalIndex}"
                                           value="${displayValue}"
                                           onchange="updateGlobalProperty('${name}', this.value)"
                                           placeholder="${name}">
                                    <button class="btn-edit" onclick="focusGlobalParam('${globalIndex}')"><i class="fas fa-edit"></i></button>
                                </div>
                            </div>
                        `;
                    });
                }
                
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

// Update global property value
function updateGlobalProperty(key, value) {
    if (!wizardData.propertyOverrides) {
        wizardData.propertyOverrides = {};
    }
    wizardData.propertyOverrides[key] = value;
    console.log('Global property updated:', key, '=', value);
}

// Focus on parameter input
function focusParam(index) {
    const input = document.getElementById(`param-${index}`);
    if (input) {
        input.focus();
        input.select();
    }
}

// Focus on global parameter input
function focusGlobalParam(index) {
    const input = document.getElementById(`param-${index}`);
    if (input) {
        input.focus();
        input.select();
    }
}

// Filter parameters based on search input
function filterParameters() {
    const searchInput = document.getElementById('paramSearch');
    if (!searchInput) return;
    
    const searchTerm = searchInput.value.toLowerCase();
    const paramItems = document.querySelectorAll('.param-item');
    const sectionHeaders = document.querySelectorAll('.param-section-header');
    
    let triggerParamsVisible = 0;
    let globalParamsVisible = 0;
    let inGlobalSection = false;
    
    paramItems.forEach(item => {
        const paramName = item.getAttribute('data-param-name');
        
        // Check if we've reached global section
        const prevSibling = item.previousElementSibling;
        if (prevSibling && prevSibling.classList.contains('param-section-header')) {
            const headerText = prevSibling.textContent.toLowerCase();
            if (headerText.includes('global')) {
                inGlobalSection = true;
            }
        }
        
        if (paramName && paramName.includes(searchTerm)) {
            item.style.display = '';
            if (inGlobalSection) {
                globalParamsVisible++;
            } else {
                triggerParamsVisible++;
            }
        } else {
            item.style.display = 'none';
        }
    });
    
    // Show/hide section headers based on visible items
    sectionHeaders.forEach(header => {
        const headerText = header.textContent.toLowerCase();
        if (headerText.includes('trigger') && triggerParamsVisible === 0) {
            header.style.display = 'none';
        } else if (headerText.includes('global') && globalParamsVisible === 0) {
            header.style.display = 'none';
        } else {
            header.style.display = '';
        }
    });
}

// Execute action
async function executeAction() {
    // For CD pipelines with FCP triggers, always set both branch parameters to fcp-classic-pipeline
    if (wizardData.mode === 'trigger' && wizardData.pipelineType === 'cd') {
        const isFCP = wizardData.trigger.name.toLowerCase().includes('fcp');
        
        if (isFCP) {
            // Always set both branches to fcp-classic-pipeline for FCP CD triggers
            wizardData.propertyOverrides['one-pipeline-config-branch'] = 'fcp-classic-pipeline';
            wizardData.propertyOverrides['pipeline-config-branch'] = 'fcp-classic-pipeline';
            console.log('FCP CD trigger detected - setting both branches to fcp-classic-pipeline');
        }
    }
    
    // For CI pipelines, don't set the one-pipeline-config-branch parameter
    if (wizardData.mode === 'trigger' && wizardData.pipelineType === 'ci') {
        // Remove one-pipeline-config-branch if it was set
        delete wizardData.propertyOverrides['one-pipeline-config-branch'];
        console.log('CI pipeline - removed one-pipeline-config-branch parameter');
    }
    
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
                // Add clickable button to open pipeline
                addPipelineButton(result.url, wizardData.trigger.name);
            }
            addLog('');
            addLog('Fetching pipeline logs...');
            
            // Store pipeline info for polling
            wizardData.pipelineId = result.pipeline_id;
            wizardData.runId = result.run_id;
            
            // Start polling for logs
            pollPipelineLogs();
        } else {
            addLog(`✗ Error: ${result.error}`, 'error');
            updateStatus('Execution failed');
            showDoneButton();
        }
    } catch (error) {
        console.error('Execution error:', error);
        addLog(`✗ Error: ${error.message}`, 'error');
        updateStatus('Execution failed');
        showDoneButton();
    }
}

// Poll pipeline logs
let pollInterval = null;
let lastTaskCount = 0;

async function pollPipelineLogs() {
    if (!wizardData.pipelineId || !wizardData.runId) {
        return;
    }
    
    try {
        const response = await fetch('/api/fcp/pipeline-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pipeline_id: wizardData.pipelineId,
                run_id: wizardData.runId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const status = result.status;
            const taskRuns = result.task_runs || [];
            
            // Display new tasks
            if (taskRuns.length > lastTaskCount) {
                for (let i = lastTaskCount; i < taskRuns.length; i++) {
                    const task = taskRuns[i];
                    const statusIcon = getTaskStatusIcon(task.status);
                    addLog(`${statusIcon} Task: ${task.name} - ${task.status}`);
                }
                lastTaskCount = taskRuns.length;
            }
            
            // Update overall status
            updateStatus(`Pipeline Status: ${status}`);
            
            // Check if pipeline is complete
            if (status === 'succeeded' || status === 'failed' || status === 'error') {
                if (pollInterval) {
                    clearInterval(pollInterval);
                    pollInterval = null;
                }
                
                addLog('');
                if (status === 'succeeded') {
                    addLog('✓ Pipeline completed successfully!', 'success');
                    updateStatus('Execution completed successfully!');
                } else {
                    addLog(`✗ Pipeline ${status}`, 'error');
                    updateStatus(`Execution ${status}`);
                }
                
                showDoneButton();
                return;
            }
            
            // Continue polling if not complete
            if (!pollInterval) {
                pollInterval = setInterval(pollPipelineLogs, 5000); // Poll every 5 seconds
            }
        } else {
            addLog(`Warning: Could not fetch pipeline status - ${result.error}`, 'error');
            if (pollInterval) {
                clearInterval(pollInterval);
                pollInterval = null;
            }
            showDoneButton();
        }
    } catch (error) {
        console.error('Polling error:', error);
        addLog(`Warning: Error polling pipeline status - ${error.message}`, 'error');
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
        showDoneButton();
    }
}

// Get task status icon
function getTaskStatusIcon(status) {
    switch (status.toLowerCase()) {
        case 'succeeded':
            return '✓';
        case 'failed':
        case 'error':
            return '✗';
        case 'running':
            return '⟳';
        case 'pending':
            return '○';
        default:
            return '•';
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
            } else if (result.worker_not_found) {
                // Worker not found, show modal with creation details
                addLog(`⚠ Worker not found for ${dc}: ${result.expected_worker}`, 'warning');
                addLog(`Opening worker creation guide...`, 'info');
                
                // Show modal with worker creation details
                showWorkerModal(dc, result.expected_worker, wizardData.toolchain.toolchain_guid);
                failCount++;
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

// Add pipeline button with color coding based on DC name
function addPipelineButton(url, triggerName) {
    const logContent = document.getElementById('logContent');
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'pipeline-button-container';
    buttonContainer.style.cssText = 'margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 8px;';
    
    // Extract DC from trigger name and determine color
    const dcColor = getDCColor(triggerName);
    
    const button = document.createElement('a');
    button.href = url;
    button.target = '_blank';
    button.className = 'btn btn-pipeline';
    button.style.cssText = `
        display: inline-block;
        padding: 12px 24px;
        background: ${dcColor};
        color: white;
        text-decoration: none;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    `;
    button.innerHTML = `<i class="fas fa-external-link-alt"></i> Open Pipeline: ${triggerName}`;
    
    // Add hover effect
    button.onmouseover = function() {
        this.style.transform = 'translateY(-2px)';
        this.style.boxShadow = '0 4px 12px rgba(0,0,0,0.25)';
    };
    button.onmouseout = function() {
        this.style.transform = 'translateY(0)';
        this.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
    };
    
    buttonContainer.appendChild(button);
    logContent.appendChild(buttonContainer);
    logContent.scrollTop = logContent.scrollHeight;
}

// Get color based on DC name
function getDCColor(triggerName) {
    const name = triggerName.toLowerCase();
    
    // Extract DC identifier from trigger name
    if (name.includes('lon')) {
        return '#0f62fe'; // Blue for London
    } else if (name.includes('syd')) {
        return '#24a148'; // Green for Sydney
    } else if (name.includes('osa')) {
        return '#d12771'; // Pink/Magenta for Osaka
    } else if (name.includes('tok')) {
        return '#8a3ffc'; // Purple for Tokyo
    } else if (name.includes('dal')) {
        return '#ff832b'; // Orange for Dallas
    } else if (name.includes('wdc') || name.includes('was')) {
        return '#fa4d56'; // Red for Washington DC
    } else if (name.includes('fra')) {
        return '#198038'; // Dark Green for Frankfurt
    } else if (name.includes('tor')) {
        return '#002d9c'; // Dark Blue for Toronto
    } else {
        return '#6929c4'; // Default Purple
    }
}

function showDoneButton() {
    document.getElementById('doneBtn').style.display = 'inline-block';
    document.querySelector('.status-indicator i').className = 'fas fa-check-circle';
}

// Made with Bob

// Worker Modal Functions
function showWorkerModal(dc, workerName, toolchainGuid) {
    const modal = document.getElementById('workerModal');
    const smSecret = `FCP-${dc.toUpperCase()}-SERVICEID-TEKTON-CDWORKER`;
    const smReference = `ref://secrets-manager.us-south.Default.Secrets%20Manager-Production/CICD/${smSecret}`;
    
    // Set values
    document.getElementById('workerNameDisplay').textContent = workerName;
    document.getElementById('workerName').value = workerName;
    document.getElementById('smSecret').value = smSecret;
    document.getElementById('smReference').value = smReference;
    
    // Store toolchain GUID for later use
    modal.dataset.toolchainGuid = toolchainGuid;
    
    // Show modal
    modal.style.display = 'flex';
}

function closeWorkerModal() {
    const modal = document.getElementById('workerModal');
    modal.style.display = 'none';
}

function copyToClipboard(elementId) {
    const input = document.getElementById(elementId);
    input.select();
    input.setSelectionRange(0, 99999); // For mobile devices
    
    try {
        document.execCommand('copy');
        
        // Show feedback
        const button = event.target.closest('.btn-copy');
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i>';
        button.style.background = '#10b981';
        
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.style.background = '';
        }, 2000);
    } catch (err) {
        console.error('Failed to copy:', err);
        alert('Failed to copy to clipboard');
    }
}

function openToolchainInBrowser() {
    const modal = document.getElementById('workerModal');
    const toolchainGuid = modal.dataset.toolchainGuid;
    const url = `https://cloud.ibm.com/devops/toolchains/${toolchainGuid}?env_id=ibm:yp:us-south`;
    window.open(url, '_blank');
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('workerModal');
    if (event.target === modal) {
        closeWorkerModal();
    }
}

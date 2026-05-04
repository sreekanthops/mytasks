// Voice Assistant - Always Listening Mode
console.log('Voice assistant script loading...');
let isListening = false;
let synthesis = window.speechSynthesis;
let voiceButton = null;

function checkAutoStart() {
    const wasActive = localStorage.getItem('voiceAssistantActive');
    if (wasActive === 'true') {
        console.log('Auto-starting voice assistant...');
        setTimeout(() => {
            if (voiceButton) {
                window.toggleVoiceAssistant();
            }
        }, 1000);
    }
}

function initVoiceAssistant() {
    console.log('Initializing voice assistant...');
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.error('Speech recognition not supported');
        return false;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = function() {
        console.log('Voice recognition started');
        isListening = true;
        localStorage.setItem('voiceAssistantActive', 'true');
        if (voiceButton) {
            voiceButton.innerHTML = '<i class="fas fa-microphone"></i><span>Voice Assistant</span>';
            voiceButton.classList.add('active');
        }
    };

    recognition.onend = function() {
        if (isListening && localStorage.getItem('voiceAssistantActive') === 'true') {
            try {
                recognition.start();
            } catch (e) {
                console.log('Could not restart:', e);
            }
        }
    };

    recognition.onresult = function(event) {
        const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase().trim();
        console.log('Heard:', transcript);
        
        // Process EVERY command directly - no wake word needed!
        processCommand(transcript);
    };

    recognition.onerror = function(event) {
        console.error('Speech error:', event.error);
        if (event.error === 'not-allowed') {
            localStorage.setItem('voiceAssistantActive', 'false');
        }
    };

    return true;
}

function processCommand(command) {
    console.log('Processing command:', command);
    
    // Navigation commands
    if (command.includes('open') || command.includes('show') || command.includes('go')) {
        if (command.includes('link')) {
            speak('Opening dashboard links');
            setTimeout(() => window.location.href = '/links', 800);
        } else if (command.includes('task')) {
            speak('Opening tasks');
            setTimeout(() => window.location.href = '/tasks', 800);
        } else if (command.includes('reminder')) {
            speak('Opening reminders');
            setTimeout(() => window.location.href = '/reminders', 800);
        } else if (command.includes('github')) {
            speak('Opening GitHub');
            setTimeout(() => window.location.href = '/github', 800);
        } else if (command.includes('setting')) {
            speak('Opening settings');
            setTimeout(() => window.location.href = '/settings', 800);
        } else if (command.includes('dashboard') || command.includes('home')) {
            speak('Opening dashboard');
            setTimeout(() => window.location.href = '/', 800);
        }
    }
    // Search commands
    else if (command.includes('search')) {
        let term = command.replace('search', '').trim();
        let env = null;
        
        // Extract environment
        if (term.includes(' in ') || term.includes(' for ')) {
            const parts = term.split(/ in | for /);
            term = parts[0].trim();
            env = parts[1] ? parts[1].trim() : null;
        }
        
        console.log('Search term:', term, 'Environment:', env);
        
        if (window.location.pathname !== '/links') {
            speak('Going to dashboard links');
            localStorage.setItem('pendingSearch', term);
            if (env) localStorage.setItem('pendingEnv', env);
            setTimeout(() => window.location.href = '/links', 800);
        } else {
            executeSearch(term, env);
        }
    }
    // Create commands
    else if (command.includes('create') || command.includes('add') || command.includes('new')) {
        if (command.includes('task')) {
            speak('Opening new task form');
            if (typeof openModal === 'function') openModal('task-modal');
        } else if (command.includes('reminder')) {
            speak('Opening new reminder form');
            if (typeof openModal === 'function') openModal('reminder-modal');
        } else if (command.includes('link')) {
            speak('Opening new link form');
            if (typeof openModal === 'function') {
                openModal('link-modal');
                if (typeof loadEnvironments === 'function') loadEnvironments();
            }
        }
    }
}

function executeSearch(term, env) {
    const searchInput = document.getElementById('link-search');
    if (searchInput) {
        searchInput.value = term;
        
        // Set environment filter if specified
        if (env) {
            const envFilter = document.getElementById('env-filter');
            if (envFilter) {
                const options = Array.from(envFilter.options);
                const match = options.find(opt => 
                    opt.text.toLowerCase().includes(env.toLowerCase())
                );
                if (match) {
                    envFilter.value = match.value;
                    speak('Searching for ' + term + ' in ' + env);
                    if (typeof loadLinks === 'function') loadLinks();
                } else {
                    speak('Searching for ' + term);
                }
            }
        } else {
            speak('Searching for ' + term);
        }
        
        if (typeof searchLinks === 'function') searchLinks();
    }
}

function speak(text) {
    console.log('Speaking:', text);
    if (synthesis.speaking) synthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    synthesis.speak(utterance);
}

window.toggleVoiceAssistant = function() {
    console.log('Toggle clicked');
    if (isListening) {
        if (recognition) recognition.stop();
        isListening = false;
        localStorage.setItem('voiceAssistantActive', 'false');
        if (voiceButton) {
            voiceButton.innerHTML = '<i class="fas fa-microphone-slash"></i><span>Voice Assistant</span>';
            voiceButton.classList.remove('active');
        }
        speak('Voice assistant stopped');
    } else {
        if (!recognition && !initVoiceAssistant()) return;
        try {
            recognition.start();
            showNotification('Voice assistant active - just speak your commands!', 'success');
        } catch (error) {
            console.error('Start error:', error);
        }
    }
};

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    voiceButton = document.getElementById('voice-btn');
    if (voiceButton) {
        console.log('Voice button found');
        voiceButton.addEventListener('click', function(e) {
            e.preventDefault();
            window.toggleVoiceAssistant();
        });
    }
    
    // Execute pending search
    const pendingSearch = localStorage.getItem('pendingSearch');
    const pendingEnv = localStorage.getItem('pendingEnv');
    if (pendingSearch && window.location.pathname === '/links') {
        console.log('Executing pending search:', pendingSearch, pendingEnv);
        setTimeout(() => {
            executeSearch(pendingSearch, pendingEnv);
            localStorage.removeItem('pendingSearch');
            localStorage.removeItem('pendingEnv');
        }, 500);
    }
    
    checkAutoStart();
});

console.log('Voice assistant script loaded');

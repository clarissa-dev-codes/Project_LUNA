document.addEventListener('DOMContentLoaded', () => {
    startDashboardClock();
    initializeTerminalInput();
    setupScratchpadAutoSave(); //the saver pipeline
    setupMoonInteraction(); //for the interactive moon in the middle (LUNA)
});

function setupMoonInteraction() {
    const moonCore = document.getElementById('luna-core');
    const terminalFeed = document.getElementById('terminal-feed');
    if (!moonCore || !terminalFeed) return;

    let isListening = false;

    moonCore.addEventListener('click', () => {
        isListening = !isListening;

        // Generate a localized clean timestamp
        const timeNow = new Date().toTimeString().split(' ')[0];

        if (isListening) {
            // Switch classes to fire off the active listening pulse animation
            moonCore.classList.remove('state-idle');
            moonCore.classList.add('state-listening');

            // Log the action to the terminal view window
            terminalFeed.innerHTML += `<br>[${timeNow}] <span style="color: #ffffff;">Luna:</span> Systems alert. Listening mode active...`;
        } else {
            // Revert back to the calm breathing loop
            moonCore.classList.remove('state-listening');
            moonCore.classList.add('state-idle');

            terminalFeed.innerHTML += `<br>[${timeNow}] <span style="color: var(--card-slate-shadow);">Luna:</span> Standing by, sir.`;
        }

        // Automatically scroll the terminal feed to the bottom so logs stay visible
        terminalFeed.scrollTop = terminalFeed.scrollHeight;

        // Send a quick notification back to the Python terminal log too
        if (window.pywebview) {
            pywebview.api.send_to_terminal(`State switched. Active listening: ${isListening}`);
        }
    });
}

function setupScratchpadAutoSave() {
    const textarea = document.getElementById('scratchpad');
    if (!textarea) return;

    let saveTimeout;

    // 1. Wait for pywebview to load, then request previous save file
    window.addEventListener('pywebviewready', async () => {
        try {
            const savedContent = await pywebview.api.load_scratchpad();
            textarea.value = savedContent;
        } catch (err) {
            console.error("Failed to load past session data:", err);
        }
    });

    // 2. Listen to typing actions inside the box
    textarea.addEventListener('input', () => {
        // Clear the previous timer every time a new key is pressed
        clearTimeout(saveTimeout);

        // Wait 800ms after you STOP typing before executing the file save to hard drive
        saveTimeout = setTimeout(async () => {
            try {
                await pywebview.api.save_scratchpad(textarea.value);
                console.log("L.U.N.A. Core: Notes saved successfully.");
            } catch (err) {
                console.error("Auto-save pipeline error:", err);
            }
        }, 800); 
    });
}


function startDashboardClock() {
    const clockElement = document.getElementById('dashboard-clock');
    function updateTime() {
        const now = new Date();
        clockElement.textContent = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    }
    updateTime();
    setInterval(updateTime, 1000);
}

window.updateHardwareMetrics = function(cpu, ram, battery) {
    const cpuEl = document.getElementById('cpu-load');
    const ramEl = document.getElementById('ram-usage');
    const batEl = document.getElementById('bat-level');
    
    if (cpuEl) cpuEl.textContent = `${cpu}%`;
    if (ramEl) ramEl.textContent = `${ram}%`;
    if (batEl) {
        batEl.textContent = battery === "100" ? "A/C Power" : `${battery}%`;
    }
}


function initializeTerminalInput() {
    const inputBox = document.getElementById('terminal-input-box');
    const terminalFeed = document.getElementById('terminal-feed');
    if (!inputBox || !terminalFeed) return;

    inputBox.addEventListener('keydown', async (event) => {
        if (event.key === 'Enter') {
            const rawText = inputBox.value.trim();
            if (!rawText) return;

            inputBox.value = ''; // Clear box
            const timeNow = new Date().toTimeString().split(' ')[0];
            
            // Print user command to UI terminal
            terminalFeed.innerHTML += `<br><span style="color: #7a768f;">[${timeNow}] User:</span> ${rawText}`;
            terminalFeed.scrollTop = terminalFeed.scrollHeight;

            // ✨ THE BRIDGE SAFETY CHECK: Verify that the framework API object exists before calling it
            if (window.pywebview && window.pywebview.api) {
                try {
                    // Call Python dispatcher natively
                    const response = await window.pywebview.api.execute_ui_command(rawText);
                    
                    const logColor = response.status === 'success' ? '#ffffff' : '#948fb0';
                    terminalFeed.innerHTML += `<br><span style="color: var(--text-frosted-lilac);">[${timeNow}] Luna:</span> <span style="color: ${logColor};">${response.msg}</span>`;
                } catch (err) {
                    terminalFeed.innerHTML += `<br><span style="color: #ff0055;">[System Error]:</span> Python function exception: ${err.message}`;
                }
            } else {
                terminalFeed.innerHTML += `<br><span style="color: #ff0055;">[System Error]:</span> L.U.N.A. API bridge offline. Try restarting.`;
            }
            terminalFeed.scrollTop = terminalFeed.scrollHeight;
        }
    });
}


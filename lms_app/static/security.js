/* Exam Shield Security Module - Strict Mode */

let violationCount = 0;
const MAX_VIOLATIONS = 1;
let isLocked = false;

document.addEventListener('DOMContentLoaded', () => {

    // 1. Block Context Menu
    document.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        showWarning("Right-click disabled.");
    });

    // 2. Block Copy/Paste
    ['copy', 'cut', 'paste'].forEach(event => {
        document.addEventListener(event, (e) => {
            e.preventDefault();
            showWarning(`${event.toUpperCase()} disabled.`);
        });
    });

    // 3. Focus Loss Detection (The main solution for App Switching)
    // When a user Alt-Tabs, the window loses focus. We immediately BLOCK the screen.
    window.addEventListener('blur', () => {
        if (!isLocked) {
            triggerLockout("External App Switch Detected");
        }
    });

    // 4. Visibility Change (Tab Switching)
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && !isLocked) {
            triggerLockout("Tab Switch Detected");
        }
    });

    // 5. CSS User Select Block
    document.body.style.userSelect = 'none';
    document.body.style.webkitUserSelect = 'none';

});

// --- Security Functions ---

function triggerLockout(reason) {
    isLocked = true;
    violationCount++;
    console.warn(`VIOLATION ${violationCount}: ${reason}`);

    // Log to Backend (NEW)
    fetch('/api/log_flag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            attempt_id: 9012, // In production, this comes from session
            flag_type: reason,
            severity: 'high'
        })
    }).catch(err => console.error("Logging failed:", err));

    // Create Blocking Overlay
    const overlay = document.createElement('div');
    overlay.id = 'security-lockout';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100vw';
    overlay.style.height = '100vh';
    overlay.style.backgroundColor = '#dc3545'; // Red
    overlay.style.zIndex = '100000';
    overlay.style.display = 'flex';
    overlay.style.flexDirection = 'column';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
    overlay.style.color = 'white';
    overlay.style.textAlign = 'center';

    overlay.innerHTML = `
        <div style="background: white; color: #333; padding: 40px; border-radius: 12px; max-width: 600px; box-shadow: 0 20px 50px rgba(0,0,0,0.5);">
            <div style="font-size: 4rem; margin-bottom: 20px;">🚨</div>
            <h1 style="color: #dc3545; margin-bottom: 10px;">EXAM LOCKED</h1>
            <h3 style="margin-bottom: 20px;">Focus Lost: You left the exam window.</h3>
            <p style="font-size: 1.1rem; margin-bottom: 20px;">
                Switching to other applications or tabs is strictly prohibited.<br>
                This incident has been flagged to the integrity officer.
            </p>
            <div style="background: #eee; padding: 10px; border-radius: 4px; margin-bottom: 30px; font-weight: bold;">
                Violation Signal: ${violationCount} / ${MAX_VIOLATIONS}
            </div>
            <button id="resume-btn" style="background: #dc3545; color: white; border: none; padding: 15px 40px; font-size: 1.2rem; font-weight: bold; border-radius: 6px; cursor: pointer;">
                ${violationCount >= MAX_VIOLATIONS ? 'TERMINATE SESSION' : 'RETURN TO EXAM'}
            </button>
        </div>
    `;

    document.body.appendChild(overlay);

    // Resume Logic
    document.getElementById('resume-btn').onclick = () => {
        overlay.remove();
        isLocked = false;

        // Auto-fail logic
        if (violationCount >= MAX_VIOLATIONS) {
            alert("❌ Integrity Failure: Too many violations. Your exam has been terminated.");
            window.location.href = "/courses.html";
        }
    };
}

function showWarning(msg) {
    const toast = document.createElement('div');
    toast.innerText = `⚠️ ${msg}`;
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.left = '50%';
    toast.style.transform = 'translateX(-50%)';
    toast.style.backgroundColor = '#333';
    toast.style.color = '#fff';
    toast.style.padding = '10px 20px';
    toast.style.borderRadius = '50px';
    toast.style.zIndex = '9999';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2000);
}

// Logic for switching tabs seamlessly without refreshing the page
document.querySelectorAll('.nav-links li').forEach(li => {
    li.addEventListener('click', () => {
        document.querySelectorAll('.nav-links li').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
        
        li.classList.add('active');
        document.getElementById(li.dataset.tab).classList.add('active');
    });
});

let rulesChart = null;

// Fetch Stats from the Backend API and update UI
async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        
        // Update number widgets using a smooth numerical counting animation
        animateValue('stat-total-requests', parseInt(document.getElementById('stat-total-requests').innerText) || 0, data.total_requests, 1000);
        animateValue('stat-total-blocked', parseInt(document.getElementById('stat-total-blocked').innerText) || 0, data.blocked_requests, 1000);
        animateValue('stat-total-allowed', parseInt(document.getElementById('stat-total-allowed').innerText) || 0, data.total_requests - data.blocked_requests, 1000);
        
        // Update Chart.js Doughnut Chart
        const labels = Object.keys(data.rule_breakdown);
        const values = Object.values(data.rule_breakdown);
        
        if (rulesChart) {
            rulesChart.data.labels = labels;
            rulesChart.data.datasets[0].data = values;
            rulesChart.update();
        } else {
            const ctx = document.getElementById('rulesChart').getContext('2d');
            rulesChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: [
                            '#3b82f6', '#ef4444', '#10b981', '#8b5cf6', '#f59e0b', '#06b6d4'
                        ],
                        borderWidth: 0,
                        hoverOffset: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right', labels: { color: '#f8fafc', font: { family: 'Outfit' } } }
                    },
                    cutout: '75%'
                }
            });
        }
    } catch (e) { console.error("Failed to load stats", e); }
}

// Helper to animate numbers counting up
function animateValue(id, start, end, duration) {
    if (start === end) return;
    let range = end - start;
    let current = start;
    let increment = end > start ? 1 : -1;
    let stepTime = Math.abs(Math.floor(duration / range));
    if (stepTime < 1) stepTime = 1;
    let obj = document.getElementById(id);
    let timer = setInterval(function() {
        current += increment;
        obj.innerHTML = current;
        if (current == end) {
            clearInterval(timer);
        }
    }, stepTime);
}

// Fetch Rules and build the configuration cards dynamically
async function loadRules() {
    try {
        const res = await fetch('/api/rules');
        const rules = await res.json();
        
        const container = document.getElementById('rules-container');
        container.innerHTML = '';
        
        // Build a card for each rule returned by the API
        for (const [name, data] of Object.entries(rules)) {
            const card = document.createElement('div');
            card.className = 'rule-card glass-panel fade-in';
            card.innerHTML = `
                <div class="rule-header">
                    <h3>${name}</h3>
                    <label class="switch">
                        <input type="checkbox" id="toggle-${name}" ${data.is_enabled ? 'checked' : ''}>
                        <span class="slider"></span>
                    </label>
                </div>
                <textarea id="config-${name}" class="rule-config">${JSON.stringify(data.config, null, 4)}</textarea>
                <button class="save-btn" onclick="saveRule('${name}')">Save Changes</button>
            `;
            container.appendChild(card);
        }
    } catch (e) { console.error("Failed to load rules", e); }
}

// Save an individual rule configuration back to the API
async function saveRule(name) {
    const isEnabled = document.getElementById(`toggle-${name}`).checked;
    let configStr = document.getElementById(`config-${name}`).value;
    let configObj;
    
    // Validate JSON before sending to backend
    try {
        configObj = JSON.parse(configStr);
    } catch (e) {
        alert("Invalid JSON format! Please check your syntax.");
        return;
    }
    
    try {
        const res = await fetch(`/api/rules/${name}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_enabled: isEnabled, config: configObj })
        });
        
        if (res.ok) {
            // Give user immediate visual feedback
            const btn = document.querySelector(`button[onclick="saveRule('${name}')"]`);
            const oldText = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-check"></i> Saved';
            btn.style.background = '#10b981';
            setTimeout(() => { btn.innerHTML = oldText; btn.style.background = ''; }, 2000);
        } else {
            alert("API rejected the change. Check logs.");
        }
    } catch (e) { alert("Failed to save rule. Is the server running?"); }
}

// Load historical security logs from the DB
async function loadLogs() {
    try {
        const res = await fetch('/api/logs');
        const logs = await res.json();
        
        const list = document.getElementById('feed-list');
        list.innerHTML = '';
        
        // Reverse so the newest items are inserted at the top of the UI
        logs.reverse().forEach(log => appendLog(log));
    } catch (e) { console.error("Failed to load logs", e); }
}

// Helper to inject a new log line into the Live Feed
function appendLog(log) {
    const list = document.getElementById('feed-list');
    const time = new Date(log.timestamp).toLocaleTimeString();
    
    const div = document.createElement('div');
    div.className = 'feed-item';
    div.innerHTML = `
        <span style="color: #94a3b8; font-family: monospace;">${time}</span>
        <span style="font-family: monospace; color: var(--text-primary);">${log.client_ip}</span>
        <span class="tag tag-rule">${log.rule_name}</span>
        <span><span class="tag tag-method" style="margin-right: 5px;">${log.method || 'GET'}</span> <span style="font-family: monospace;">${log.blocked_path || '/'}</span></span>
        <span style="color: #ef4444; font-size: 0.9rem;">${log.reason}</span>
    `;
    list.prepend(div);
}

// Real-time WebSocket connection to the gateway
function setupWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/live-feed`);
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        // Inject current timestamp since this just happened live!
        data.timestamp = new Date().toISOString();
        
        // Add to live feed UI
        appendLog(data);
        
        // Silently refresh the charts and numbers so they tick up instantly
        loadStats();
    };
    
    ws.onclose = function() {
        console.log("WebSocket disconnected. Reconnecting in 5s...");
        setTimeout(setupWebSocket, 5000);
    };
}

// Boot up sequence
window.onload = () => {
    loadStats();
    loadRules();
    loadLogs();
    setupWebSocket();
    
    // Refresh stats periodically (every 10 seconds) just as a fallback 
    setInterval(loadStats, 10000);
};

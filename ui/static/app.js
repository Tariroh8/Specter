document.addEventListener("DOMContentLoaded", () => {
    // Navigation Logic
    const navDashboard = document.getElementById("nav-dashboard");
    const navTimeline = document.getElementById("nav-timeline");
    const navChats = document.getElementById("nav-chats");
    const navTasks = document.getElementById("nav-tasks");
    const navSettings = document.getElementById("nav-settings");
    const viewDashboard = document.getElementById("view-dashboard");
    const viewTimeline = document.getElementById("view-timeline");
    const viewChats = document.getElementById("view-chats");
    const viewTasks = document.getElementById("view-tasks");
    const viewSkills = document.getElementById("view-skills");
    const viewSettings = document.getElementById("view-settings");

    function switchView(navEl, viewEl) {
        [navDashboard, navTimeline, navChats, navTasks, navSkills, navSettings].forEach(el => el.classList.remove("active"));
        [viewDashboard, viewTimeline, viewChats, viewTasks, viewSkills, viewSettings].forEach(el => el.classList.remove("active"));
        navEl.classList.add("active");
        viewEl.classList.add("active");
    }

    navDashboard.addEventListener("click", (e) => {
        e.preventDefault();
        switchView(navDashboard, viewDashboard);
        fetchStats();
    });

    navTimeline.addEventListener("click", (e) => {
        e.preventDefault();
        switchView(navTimeline, viewTimeline);
        fetchEvents();
    });

    navChats.addEventListener("click", (e) => {
        e.preventDefault();
        switchView(navChats, viewChats);
        fetchChats();
    });

    const navSkills = document.getElementById("nav-skills");
    
    navTasks.addEventListener("click", (e) => {
        e.preventDefault();
        switchView(navTasks, viewTasks);
        fetchTasks();
    });

    navSkills.addEventListener("click", (e) => {
        e.preventDefault();
        switchView(navSkills, viewSkills);
        fetchSkills();
    });

    navSettings.addEventListener("click", (e) => {
        e.preventDefault();
        switchView(navSettings, viewSettings);
        loadSettings();
    });

    // Dashboard Stats Logic
    async function fetchStats() {
        if (!viewDashboard.classList.contains("active")) return;
        try {
            const res = await fetch("/api/stats");
            const stats = await res.json();
            
            document.getElementById("stat-total-events").textContent = stats.total_events || 0;
            document.getElementById("stat-idle-count").textContent = stats.idle_count || 0;
            
            const topApps = Object.keys(stats.top_apps || {});
            document.getElementById("stat-top-app").textContent = topApps.length > 0 ? topApps[0] : "-";
            
            const topFiles = Object.keys(stats.top_files || {});
            // display just the filename not the whole path
            document.getElementById("stat-top-file").textContent = topFiles.length > 0 ? topFiles[0].split('\\').pop().split('/').pop() : "-";
            
        } catch (err) {
            console.error("Failed to fetch stats:", err);
        }
    }

    // Timeline Logic
    const timelineContainer = document.getElementById("timeline-container");
    const searchInput = document.getElementById("search-input");
    const searchBtn = document.getElementById("search-btn");
    let currentSearchQuery = "";

    async function fetchEvents() {
        if (!viewTimeline.classList.contains("active")) return;
        
        try {
            let url = "/api/events?limit=50";
            if (currentSearchQuery) {
                url = `/api/search?q=${encodeURIComponent(currentSearchQuery)}&limit=50`;
            }
            
            const res = await fetch(url);
            const events = await res.json();
            renderTimeline(events);
        } catch (err) {
            console.error("Failed to fetch events:", err);
        }
    }

    searchBtn.addEventListener("click", () => {
        currentSearchQuery = searchInput.value.trim();
        fetchEvents();
    });
    
    searchInput.addEventListener("keypress", (e) => {
        if (e.key === 'Enter') {
            currentSearchQuery = searchInput.value.trim();
            fetchEvents();
        }
    });

    function renderTimeline(events) {
        timelineContainer.innerHTML = "";
        
        if (events.length === 0) {
            timelineContainer.innerHTML = "<p style='color: var(--text-muted);'>No events found.</p>";
            return;
        }

        events.forEach(event => {
            const card = document.createElement("div");
            card.className = "event-card";
            
            // Format time (assuming UTC from DB)
            const date = new Date(event.timestamp + "Z");
            const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

            const content = event.content || "";
            const source = event.source || "";
            
            card.innerHTML = `
                <div class="event-header">
                    <span class="event-type ${event.event_type === 'BROWSER_SEARCH' ? 'search-badge' : ''} ${event.event_type === 'AI_CHAT' ? 'ai-badge' : ''}">${escapeHTML(event.event_type)}</span>
                    <span class="event-time">${timeStr}</span>
                </div>
                <div class="event-body ${event.event_type === 'BROWSER_SEARCH' ? 'search-body' : ''} ${event.event_type === 'AI_CHAT' ? 'ai-body' : ''}">${escapeHTML(content)}</div>
                ${source ? `<div class="event-source">Source: ${escapeHTML(source)}</div>` : ''}
            `;
            timelineContainer.appendChild(card);
        });
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }

    // AI Chats Logic
    const chatsContainer = document.getElementById("chats-container");
    const chatModal = document.getElementById("chat-modal");
    const modalCloseBtn = document.getElementById("modal-close");
    const modalChatTopic = document.getElementById("modal-chat-topic");
    const modalChatBody = document.getElementById("modal-chat-body");
    
    let loadedChats = [];

    async function fetchChats() {
        if (!viewChats.classList.contains("active")) return;
        try {
            const res = await fetch("/api/chats");
            loadedChats = await res.json();
            renderChats(loadedChats);
        } catch (err) {
            console.error("Failed to fetch chats:", err);
        }
    }

    function renderChats(chats) {
        chatsContainer.innerHTML = "";
        if (chats.length === 0) {
            chatsContainer.innerHTML = "<p style='color: var(--text-muted);'>No AI conversations found.</p>";
            return;
        }

        chats.forEach((chat, index) => {
            const card = document.createElement("div");
            card.className = "chat-card glass-panel";
            
            const date = new Date(chat.start_time);
            const timeStr = date.toLocaleString();
            
            card.innerHTML = `
                <div class="chat-source-badge">${escapeHTML(chat.source)}</div>
                <h3>${escapeHTML(chat.topic)}</h3>
                <div style="font-size: 0.8rem; color: var(--text-muted);">${timeStr}</div>
            `;
            
            card.addEventListener("click", () => openChatModal(index));
            chatsContainer.appendChild(card);
        });
    }

    function openChatModal(index) {
        const chat = loadedChats[index];
        if (!chat) return;
        
        modalChatTopic.textContent = chat.topic;
        modalChatBody.innerHTML = formatChatTranscript(chat.content);
        chatModal.style.display = "flex";
    }
    
    modalCloseBtn.addEventListener("click", () => {
        chatModal.style.display = "none";
    });
    
    chatModal.addEventListener("click", (e) => {
        if (e.target === chatModal) chatModal.style.display = "none";
    });

    function formatChatTranscript(text) {
        const lines = text.split('\n');
        let html = '';
        let currentRole = 'unknown';
        let currentBlock = [];
        
        function flushBlock() {
            if (currentBlock.length === 0) return;
            const blockText = currentBlock.join('\n').trim();
            if (blockText) {
                const safeText = escapeHTML(blockText).replace(/\n/g, '<br>');
                const roleClass = (currentRole === 'USER') ? 'user' : 'ai';
                html += `
                    <div class="chat-bubble-container ${roleClass}">
                        <div class="chat-bubble ${roleClass}">${safeText}</div>
                    </div>
                `;
            }
            currentBlock = [];
        }
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line.match(/^\[[A-Z]+\]$/)) {
                flushBlock();
                currentRole = line.replace(/[\[\]]/g, '');
            } else {
                currentBlock.push(lines[i]);
            }
        }
        flushBlock();
        return html;
    }

    // Tasks Logic
    const tasksContainer = document.getElementById("tasks-container");
    
    async function fetchTasks() {
        if (!viewTasks.classList.contains("active")) return;
        try {
            const res = await fetch("/api/tasks");
            const tasks = await res.json();
            renderTasks(tasks);
        } catch (err) {
            console.error("Failed to fetch tasks:", err);
        }
    }

    function renderTasks(tasks) {
        tasksContainer.innerHTML = "";
        if (tasks.length === 0) {
            tasksContainer.innerHTML = "<p style='color: var(--text-muted);'>No delegated tasks found.</p>";
            return;
        }

        tasks.forEach(task => {
            const card = document.createElement("div");
            card.className = "task-card glass-panel";
            
            const isRunning = task.status === 'running';
            const statusClass = isRunning ? 'status-running' : `status-${task.status}`;
            
            card.innerHTML = `
                <div class="task-header">
                    <h3 style="margin:0; font-size:1.1rem; color: var(--accent-blue);">${escapeHTML(task.name)}</h3>
                    <span class="task-status ${statusClass}" style="font-size: 0.8rem; padding: 2px 6px; border-radius: 4px; background: rgba(255,255,255,0.1);">${escapeHTML(task.status.toUpperCase())}</span>
                </div>
                <div class="task-body" style="margin: 10px 0; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px;">
                    <code style="color: var(--text-muted); word-break: break-all;">${escapeHTML(task.command)}</code>
                </div>
                <div class="task-footer" style="display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; color: var(--text-muted);">
                    <span>PID: ${task.pid || 'N/A'}</span>
                    ${isRunning ? `<button class="btn-primary" style="padding: 4px 10px; font-size: 0.8rem; background: #e74c3c;" onclick="stopTask(${task.id})">Stop</button>` : ''}
                </div>
            `;
            tasksContainer.appendChild(card);
        });
    }

    window.stopTask = async function(taskId) {
        try {
            const res = await fetch(`/api/tasks/${taskId}/stop`, { method: "POST" });
            if (res.ok) {
                fetchTasks();
            } else {
                alert("Failed to stop task.");
            }
        } catch (err) {
            console.error("Failed to stop task:", err);
        }
    };

    // Skills Logic
    const skillsContainer = document.getElementById("skills-container");

    async function fetchSkills() {
        if (!viewSkills.classList.contains("active")) return;
        try {
            const res = await fetch("/api/skills");
            const skills = await res.json();
            renderSkills(skills);
        } catch (err) {
            console.error("Failed to fetch skills:", err);
        }
    }

    function renderSkills(skills) {
        skillsContainer.innerHTML = "";
        const skillNames = Object.keys(skills);
        if (skillNames.length === 0) {
            skillsContainer.innerHTML = "<p style='color: var(--text-muted);'>No skills loaded.</p>";
            return;
        }

        skillNames.forEach(name => {
            const meta = skills[name];
            const card = document.createElement("div");
            card.className = "skill-card glass-panel";
            card.style.padding = "15px";
            card.style.marginBottom = "15px";

            let paramsHtml = "";
            if (meta.parameters && Object.keys(meta.parameters).length > 0) {
                Object.keys(meta.parameters).forEach(param => {
                    paramsHtml += `
                        <div class="form-group" style="margin-bottom: 8px;">
                            <label style="font-size: 0.8rem; color: var(--text-muted);">${param} - ${meta.parameters[param]}</label>
                            <input type="text" id="param-${name}-${param}" placeholder="Value for ${param}" style="width: 100%; padding: 6px; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); color: white; border-radius: 4px;">
                        </div>
                    `;
                });
            }

            card.innerHTML = `
                <h3 style="margin: 0 0 5px 0; color: var(--accent-blue);">${name}</h3>
                <p style="margin: 0 0 15px 0; font-size: 0.9rem; color: var(--text-muted);">${escapeHTML(meta.description)}</p>
                <div class="skill-params">
                    ${paramsHtml}
                </div>
                <button class="btn-primary" onclick="runSkill('${name}', ${JSON.stringify(Object.keys(meta.parameters || {}))})" style="margin-top: 10px;">Execute Skill</button>
                <div id="skill-result-${name}" style="margin-top: 10px; font-size: 0.85rem;"></div>
            `;
            skillsContainer.appendChild(card);
        });
    }

    window.runSkill = async function(skillName, paramsList) {
        const payload = {};
        let allGood = true;
        
        paramsList.forEach(param => {
            const val = document.getElementById(`param-${skillName}-${param}`).value.trim();
            if (val) {
                payload[param] = val;
            } else {
                // simple check for requiredness could go here, for now we just pass what's there
            }
        });

        const resultDiv = document.getElementById(`skill-result-${skillName}`);
        resultDiv.innerHTML = "<span style='color: var(--accent-blue);'>Executing...</span>";

        try {
            const res = await fetch(`/api/skills/${skillName}/run`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            if (data.success) {
                resultDiv.innerHTML = `<span style="color: #2ecc71;">✅ ${escapeHTML(data.message)}</span>`;
            } else {
                resultDiv.innerHTML = `<span style="color: #e74c3c;">❌ ${escapeHTML(data.message || 'Execution failed')}</span>`;
            }
        } catch (err) {
            console.error("Failed to execute skill:", err);
            resultDiv.innerHTML = `<span style="color: #e74c3c;">❌ Network Error</span>`;
        }
    };

    // Settings Logic
    const settingsForm = document.getElementById("settings-form");
    const statusMsg = document.getElementById("settings-status");

    async function loadSettings() {
        try {
            const res = await fetch("/api/settings");
            const config = await res.json();
            if (config.model_provider) {
                document.getElementById("model_provider").value = config.model_provider;
            }
            if (config.api_key) {
                document.getElementById("api_key").value = config.api_key;
            }
        } catch (err) {
            console.error("Failed to load settings:", err);
        }
    }

    settingsForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const data = {
            model_provider: document.getElementById("model_provider").value,
            api_key: document.getElementById("api_key").value
        };

        try {
            const res = await fetch("/api/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            });
            if (res.ok) {
                statusMsg.textContent = "Settings saved successfully.";
                setTimeout(() => { statusMsg.textContent = ""; }, 3000);
            }
        } catch (err) {
            console.error("Failed to save settings:", err);
            statusMsg.textContent = "Error saving settings.";
        }
    });

    // Initial fetch and polling
    fetchStats();
    fetchEvents();
    fetchChats();
    fetchTasks();
    setInterval(() => {
        fetchStats();
        fetchEvents();
        fetchChats();
        fetchTasks();
    }, 2000);
});

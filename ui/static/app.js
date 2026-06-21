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

    // SVG Core Node Navigation
    const svgNodes = {
        "node-timeline": { nav: navTimeline, view: viewTimeline, fetch: fetchEvents },
        "node-chats": { nav: navChats, view: viewChats, fetch: fetchChats },
        "node-tasks": { nav: navTasks, view: viewTasks, fetch: fetchTasks },
        "node-skills": { nav: navSkills, view: viewSkills, fetch: fetchSkills },
        "node-settings": { nav: navSettings, view: viewSettings, fetch: loadSettings }
    };

    Object.keys(svgNodes).forEach(nodeId => {
        const nodeEl = document.getElementById(nodeId);
        if (nodeEl) {
            nodeEl.addEventListener("click", () => {
                const node = svgNodes[nodeId];
                switchView(node.nav, node.view);
                node.fetch();
            });
        }
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

    let activeChatContent = "";
    const modalSpeakBtn = document.getElementById("modal-speak-btn");

    function openChatModal(index) {
        const chat = loadedChats[index];
        if (!chat) return;
        
        activeChatContent = chat.content;
        modalChatTopic.textContent = chat.topic;
        modalChatBody.innerHTML = formatChatTranscript(chat.content);
        chatModal.style.display = "flex";
    }
    
    modalCloseBtn.addEventListener("click", () => {
        chatModal.style.display = "none";
        activeChatContent = "";
    });
    
    chatModal.addEventListener("click", (e) => {
        if (e.target === chatModal) {
            chatModal.style.display = "none";
            activeChatContent = "";
        }
    });

    if (modalSpeakBtn) {
        modalSpeakBtn.addEventListener("click", async () => {
            if (!activeChatContent) return;

            const originalHtml = modalSpeakBtn.innerHTML;
            modalSpeakBtn.disabled = true;
            modalSpeakBtn.innerHTML = "⏳ Reading...";

            // Clean chat transcript markers into conversational sentences
            const lines = activeChatContent.split('\n');
            let speakableText = [];
            lines.forEach(line => {
                const trimmed = line.trim();
                if (trimmed === '[USER]') {
                    speakableText.push("User said:");
                } else if (trimmed === '[AI]') {
                    speakableText.push("A.I. responded:");
                } else if (trimmed) {
                    // Remove code blocks and backticks
                    const cleanLine = trimmed.replace(/```[a-z]*|```|`/gi, '').trim();
                    if (cleanLine) {
                        speakableText.push(cleanLine);
                    }
                }
            });

            const textToSpeak = speakableText.join('. ');

            try {
                await fetch('/api/skills/speak/run', {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text: textToSpeak })
                });
            } catch (err) {
                console.error("Failed to read chat:", err);
            } finally {
                modalSpeakBtn.disabled = false;
                modalSpeakBtn.innerHTML = originalHtml;
            }
        });
    }

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

    // ==========================================================================
    // INTERACTIVE TOOL CENTER LOGIC
    // ==========================================================================
    const skillsContainer = document.getElementById("skills-container");
    let loadedSkills = {};
    let activeToolCategory = "all";

    // Setup Category Filter Buttons
    const filterBtns = document.querySelectorAll(".filter-btn");
    filterBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            filterBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeToolCategory = btn.getAttribute("data-category");
            renderSkills(loadedSkills);
        });
    });

    const SKILL_ICONS = {
        social_post: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>`,
        social_comment: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
        social_login: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>`,
        local_server_tunneler: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/><path d="M2 12h20"/></svg>`,
        scaffold_project: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/><polygon points="12 11 12 17 17 14"/></svg>`,
        deploy_django_pythonanywhere: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a6 6 0 0 0 0-12z"/></svg>`,
        system_control: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/></svg>`,
        youtube_play: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>`,
        web_search: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
        fallback: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`
    };

    const SKILL_CATEGORIES = {
        social_login: "social",
        social_post: "social",
        social_comment: "social",
        local_server_tunneler: "dev",
        scaffold_project: "dev",
        deploy_django_pythonanywhere: "dev",
        delegate_to_antigravity: "dev",
        system_control: "utility",
        youtube_play: "utility",
        web_search: "utility",
        chatgpt_browser: "utility",
        restart_specter: "utility"
    };

    async function fetchSkills() {
        if (!viewSkills.classList.contains("active")) return;
        try {
            const res = await fetch("/api/skills");
            loadedSkills = await res.json();
            renderSkills(loadedSkills);
        } catch (err) {
            console.error("Failed to fetch skills:", err);
        }
    }

    async function runSkillAPI(skillName, payload, resultDiv) {
        resultDiv.className = "tool-result info";
        resultDiv.innerHTML = "⏳ Processing task. Please wait...";
        try {
            const res = await fetch(`/api/skills/${skillName}/run`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                resultDiv.className = "tool-result success";
                resultDiv.innerHTML = `✅ ${escapeHTML(data.message)}`;
            } else {
                resultDiv.className = "tool-result error";
                resultDiv.innerHTML = `❌ ${escapeHTML(data.message || 'Execution failed')}`;
            }
        } catch (err) {
            resultDiv.className = "tool-result error";
            resultDiv.innerHTML = `❌ Connection Error`;
        }
    }

    function renderSkills(skills) {
        skillsContainer.innerHTML = "";
        const skillNames = Object.keys(skills);
        
        if (skillNames.length === 0) {
            skillsContainer.innerHTML = "<p style='color: var(--text-muted);'>No skills loaded.</p>";
            return;
        }

        // Filter skills
        const filteredNames = skillNames.filter(name => {
            const cat = SKILL_CATEGORIES[name] || "utility";
            return activeToolCategory === "all" || cat === activeToolCategory;
        });

        if (filteredNames.length === 0) {
            skillsContainer.innerHTML = "<p style='color: var(--text-muted);'>No tools found in this category.</p>";
            return;
        }

        filteredNames.forEach(name => {
            const meta = skills[name];
            const cat = SKILL_CATEGORIES[name] || "utility";
            
            const card = document.createElement("div");
            card.className = `tool-card cat-${cat}`;

            const iconSvg = SKILL_ICONS[name] || SKILL_ICONS.fallback;

            if (name === "social_post") {
                card.innerHTML = `
                    <div class="tool-header">
                        <div class="tool-icon-wrapper">${iconSvg}</div>
                        <div class="tool-title-desc">
                            <span class="tool-title">Publish Content</span>
                            <span class="tool-desc">${escapeHTML(meta.description)}</span>
                        </div>
                    </div>
                    <div class="tool-body">
                        <div class="tool-field">
                            <label>Platform</label>
                            <div class="platform-segmented-control">
                                <button class="platform-seg-btn active" data-val="facebook">Facebook</button>
                                <button class="platform-seg-btn" data-val="instagram">Instagram</button>
                                <button class="platform-seg-btn" data-val="tiktok">TikTok</button>
                            </div>
                        </div>
                        <div class="tool-field">
                            <label>Post Text / Caption</label>
                            <textarea class="tool-input" id="post-text" rows="2" placeholder="What's on your mind?"></textarea>
                        </div>
                        <div class="tool-field">
                            <label>Media File Path (Image or Video)</label>
                            <input type="text" class="tool-input" id="post-media" placeholder="C:\\path\\to\\file.jpg">
                        </div>
                    </div>
                    <div class="tool-footer">
                        <button class="btn-primary btn-run">Publish Post</button>
                        <div class="tool-result"></div>
                    </div>
                `;
                setupSegmentedControl(card);
                const runBtn = card.querySelector(".btn-run");
                const resultDiv = card.querySelector(".tool-result");
                runBtn.addEventListener("click", () => {
                    const platform = card.querySelector(".platform-seg-btn.active").getAttribute("data-val");
                    const text = card.querySelector("#post-text").value.trim();
                    const media_path = card.querySelector("#post-media").value.trim();
                    runSkillAPI("social_post", { platform, text, media_path }, resultDiv);
                });

            } else if (name === "social_comment") {
                card.innerHTML = `
                    <div class="tool-header">
                        <div class="tool-icon-wrapper">${iconSvg}</div>
                        <div class="tool-title-desc">
                            <span class="tool-title">Post Comment</span>
                            <span class="tool-desc">${escapeHTML(meta.description)}</span>
                        </div>
                    </div>
                    <div class="tool-body">
                        <div class="tool-field">
                            <label>Platform</label>
                            <div class="platform-segmented-control">
                                <button class="platform-seg-btn active" data-val="facebook">Facebook</button>
                                <button class="platform-seg-btn" data-val="instagram">Instagram</button>
                                <button class="platform-seg-btn" data-val="tiktok">TikTok</button>
                            </div>
                        </div>
                        <div class="tool-field">
                            <label>Post or Video URL</label>
                            <input type="text" class="tool-input" id="comment-url" placeholder="https://...">
                        </div>
                        <div class="tool-field">
                            <label>Comment Message</label>
                            <input type="text" class="tool-input" id="comment-text" placeholder="Write your comment...">
                        </div>
                    </div>
                    <div class="tool-footer">
                        <button class="btn-primary btn-run">Post Comment</button>
                        <div class="tool-result"></div>
                    </div>
                `;
                setupSegmentedControl(card);
                const runBtn = card.querySelector(".btn-run");
                const resultDiv = card.querySelector(".tool-result");
                runBtn.addEventListener("click", () => {
                    const platform = card.querySelector(".platform-seg-btn.active").getAttribute("data-val");
                    const url = card.querySelector("#comment-url").value.trim();
                    const text = card.querySelector("#comment-text").value.trim();
                    runSkillAPI("social_comment", { platform, url, text }, resultDiv);
                });

            } else if (name === "social_login") {
                card.innerHTML = `
                    <div class="tool-header">
                        <div class="tool-icon-wrapper">${iconSvg}</div>
                        <div class="tool-title-desc">
                            <span class="tool-title">Social Authentication</span>
                            <span class="tool-desc">${escapeHTML(meta.description)}</span>
                        </div>
                    </div>
                    <div class="tool-body">
                        <div class="tool-field">
                            <label>Select Platform</label>
                            <div class="platform-segmented-control">
                                <button class="platform-seg-btn active" data-val="facebook">Facebook</button>
                                <button class="platform-seg-btn" data-val="instagram">Instagram</button>
                                <button class="platform-seg-btn" data-val="tiktok">TikTok</button>
                            </div>
                        </div>
                    </div>
                    <div class="tool-footer">
                        <button class="btn-primary btn-run">Launch Interactive Login</button>
                        <div class="tool-result"></div>
                    </div>
                `;
                setupSegmentedControl(card);
                const runBtn = card.querySelector(".btn-run");
                const resultDiv = card.querySelector(".tool-result");
                runBtn.addEventListener("click", () => {
                    const platform = card.querySelector(".platform-seg-btn.active").getAttribute("data-val");
                    runSkillAPI("social_login", { platform }, resultDiv);
                });

            } else if (name === "local_server_tunneler") {
                card.innerHTML = `
                    <div class="tool-header">
                        <div class="tool-icon-wrapper">${iconSvg}</div>
                        <div class="tool-title-desc">
                            <span class="tool-title">Local Port Tunneler</span>
                            <span class="tool-desc">${escapeHTML(meta.description)}</span>
                        </div>
                    </div>
                    <div class="tool-body">
                        <div class="tool-field">
                            <label>Action</label>
                            <div class="platform-segmented-control">
                                <button class="platform-seg-btn active" data-val="start">Start Tunnel</button>
                                <button class="platform-seg-btn" data-val="stop">Stop Tunnel</button>
                            </div>
                        </div>
                        <div class="tool-field">
                            <label>Port</label>
                            <input type="number" class="tool-input" id="tunnel-port" value="5000">
                        </div>
                        <div class="tool-field">
                            <label>Subdomain (Optional)</label>
                            <input type="text" class="tool-input" id="tunnel-subdomain" placeholder="my-custom-subdomain">
                        </div>
                    </div>
                    <div class="tool-footer">
                        <button class="btn-primary btn-run">Apply Tunnel</button>
                        <div class="tool-result"></div>
                    </div>
                `;
                setupSegmentedControl(card);
                const runBtn = card.querySelector(".btn-run");
                const resultDiv = card.querySelector(".tool-result");
                runBtn.addEventListener("click", () => {
                    const action = card.querySelector(".platform-seg-btn.active").getAttribute("data-val");
                    const port = card.querySelector("#tunnel-port").value.trim();
                    const subdomain = card.querySelector("#tunnel-subdomain").value.trim();
                    runSkillAPI("local_server_tunneler", { action, port, subdomain }, resultDiv);
                });

            } else if (name === "system_control") {
                card.innerHTML = `
                    <div class="tool-header">
                        <div class="tool-icon-wrapper">${iconSvg}</div>
                        <div class="tool-title-desc">
                            <span class="tool-title">System Power Control</span>
                            <span class="tool-desc">${escapeHTML(meta.description)}</span>
                        </div>
                    </div>
                    <div class="tool-body">
                        <label style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">Power Actions</label>
                        <div class="power-btn-grid">
                            <button class="power-action-btn action-sleep" data-action="sleep">
                                <svg viewBox="0 0 24 24" stroke="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
                                Sleep
                            </button>
                            <button class="power-action-btn action-restart" data-action="restart">
                                <svg viewBox="0 0 24 24" stroke="currentColor"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                                Restart
                            </button>
                            <button class="power-action-btn action-shutdown" data-action="shutdown">
                                <svg viewBox="0 0 24 24" stroke="currentColor"><path d="M18.36 6.64a9 9 0 1 1-12.73 0 M12 2v10"/></svg>
                                Shutdown
                            </button>
                        </div>
                    </div>
                    <div class="tool-footer">
                        <div class="tool-result"></div>
                    </div>
                `;
                const resultDiv = card.querySelector(".tool-result");
                card.querySelectorAll(".power-action-btn").forEach(btn => {
                    btn.addEventListener("click", () => {
                        const act = btn.getAttribute("data-action");
                        if (confirm(`Are you sure you want to trigger OS ${act.toUpperCase()}?`)) {
                            runSkillAPI("system_control", { action: act }, resultDiv);
                        }
                    });
                });

            } else if (name === "youtube_play") {
                card.innerHTML = `
                    <div class="tool-header">
                        <div class="tool-icon-wrapper">${iconSvg}</div>
                        <div class="tool-title-desc">
                            <span class="tool-title">YouTube Player</span>
                            <span class="tool-desc">${escapeHTML(meta.description)}</span>
                        </div>
                    </div>
                    <div class="tool-body">
                        <div class="tool-field">
                            <label>Video Search Query</label>
                            <input type="text" class="tool-input" id="yt-query" placeholder="Song name or video topic...">
                        </div>
                    </div>
                    <div class="tool-footer">
                        <button class="btn-primary btn-run">Play Video</button>
                        <div class="tool-result"></div>
                    </div>
                `;
                const runBtn = card.querySelector(".btn-run");
                const resultDiv = card.querySelector(".tool-result");
                runBtn.addEventListener("click", () => {
                    const query = card.querySelector("#yt-query").value.trim();
                    runSkillAPI("youtube_play", { query }, resultDiv);
                });

            } else if (name === "web_search") {
                card.innerHTML = `
                    <div class="tool-header">
                        <div class="tool-icon-wrapper">${iconSvg}</div>
                        <div class="tool-title-desc">
                            <span class="tool-title">Web Search</span>
                            <span class="tool-desc">${escapeHTML(meta.description)}</span>
                        </div>
                    </div>
                    <div class="tool-body">
                        <div class="tool-field">
                            <label>Google Search Query</label>
                            <input type="text" class="tool-input" id="search-query" placeholder="What do you want to find?">
                        </div>
                    </div>
                    <div class="tool-footer">
                        <button class="btn-primary btn-run">Perform Search</button>
                        <div class="tool-result"></div>
                    </div>
                `;
                const runBtn = card.querySelector(".btn-run");
                const resultDiv = card.querySelector(".tool-result");
                runBtn.addEventListener("click", () => {
                    const query = card.querySelector("#search-query").value.trim();
                    runSkillAPI("web_search", { query }, resultDiv);
                });

            } else if (name === "scaffold_project") {
                card.innerHTML = `
                    <div class="tool-header">
                        <div class="tool-icon-wrapper">${iconSvg}</div>
                        <div class="tool-title-desc">
                            <span class="tool-title">Scaffold Project</span>
                            <span class="tool-desc">${escapeHTML(meta.description)}</span>
                        </div>
                    </div>
                    <div class="tool-body">
                        <div class="tool-field">
                            <label>Project Name</label>
                            <input type="text" class="tool-input" id="scaffold-name" placeholder="my_new_app">
                        </div>
                        <div class="tool-field">
                            <label>Project Type</label>
                            <select class="tool-input" id="scaffold-type">
                                <option value="python">Python Project</option>
                                <option value="node">Node.js Project</option>
                                <option value="react">React Project</option>
                            </select>
                        </div>
                        <div class="tool-field">
                            <label>Absolute Path (Optional)</label>
                            <input type="text" class="tool-input" id="scaffold-path" placeholder="Defaults to current folder">
                        </div>
                    </div>
                    <div class="tool-footer">
                        <button class="btn-primary btn-run">Generate Project</button>
                        <div class="tool-result"></div>
                    </div>
                `;
                const runBtn = card.querySelector(".btn-run");
                const resultDiv = card.querySelector(".tool-result");
                runBtn.addEventListener("click", () => {
                    const project_name = card.querySelector("#scaffold-name").value.trim();
                    const project_type = card.querySelector("#scaffold-type").value.trim();
                    const path = card.querySelector("#scaffold-path").value.trim();
                    runSkillAPI("scaffold_project", { project_name, project_type, path }, resultDiv);
                });

            } else if (name === "deploy_django_pythonanywhere") {
                card.innerHTML = `
                    <div class="tool-header">
                        <div class="tool-icon-wrapper">${iconSvg}</div>
                        <div class="tool-title-desc">
                            <span class="tool-title">Deploy to PythonAnywhere</span>
                            <span class="tool-desc">${escapeHTML(meta.description)}</span>
                        </div>
                    </div>
                    <div class="tool-body">
                        <div class="tool-field">
                            <label>PA Username</label>
                            <input type="text" class="tool-input" id="pa-username" placeholder="your_username">
                        </div>
                        <div class="tool-field">
                            <label>PA API Token</label>
                            <input type="password" class="tool-input" id="pa-token" placeholder="API key">
                        </div>
                        <div class="tool-field">
                            <label>GitHub Repository URL</label>
                            <input type="text" class="tool-input" id="pa-github" placeholder="https://github.com/...">
                        </div>
                        <div class="tool-field">
                            <label>Custom Subdomain (Optional)</label>
                            <input type="text" class="tool-input" id="pa-domain" placeholder="username.pythonanywhere.com">
                        </div>
                    </div>
                    <div class="tool-footer">
                        <button class="btn-primary btn-run">Deploy Django App</button>
                        <div class="tool-result"></div>
                    </div>
                `;
                const runBtn = card.querySelector(".btn-run");
                const resultDiv = card.querySelector(".tool-result");
                runBtn.addEventListener("click", () => {
                    const username = card.querySelector("#pa-username").value.trim();
                    const api_token = card.querySelector("#pa-token").value.trim();
                    const github_url = card.querySelector("#pa-github").value.trim();
                    const domain = card.querySelector("#pa-domain").value.trim();
                    runSkillAPI("deploy_django_pythonanywhere", { username, api_token, github_url, domain }, resultDiv);
                });

            } else {
                // Fallback Dynamic Render Card
                let paramsHtml = "";
                const paramKeys = Object.keys(meta.parameters || {});
                paramKeys.forEach(param => {
                    paramsHtml += `
                        <div class="tool-field">
                            <label>${param}</label>
                            <input type="text" class="tool-input param-input" data-param="${param}" placeholder="${escapeHTML(meta.parameters[param])}">
                        </div>
                    `;
                });

                card.innerHTML = `
                    <div class="tool-header">
                        <div class="tool-icon-wrapper">${SKILL_ICONS.fallback}</div>
                        <div class="tool-title-desc">
                            <span class="tool-title">${escapeHTML(name)}</span>
                            <span class="tool-desc">${escapeHTML(meta.description)}</span>
                        </div>
                    </div>
                    <div class="tool-body">
                        ${paramsHtml}
                    </div>
                    <div class="tool-footer">
                        <button class="btn-primary btn-run">Run Tool</button>
                        <div class="tool-result"></div>
                    </div>
                `;
                const runBtn = card.querySelector(".btn-run");
                const resultDiv = card.querySelector(".tool-result");
                runBtn.addEventListener("click", () => {
                    const payload = {};
                    card.querySelectorAll(".param-input").forEach(inp => {
                        const param = inp.getAttribute("data-param");
                        const val = inp.value.trim();
                        if (val) payload[param] = val;
                    });
                    runSkillAPI(name, payload, resultDiv);
                });
            }

            skillsContainer.appendChild(card);
        });
    }

    function setupSegmentedControl(card) {
        const segBtns = card.querySelectorAll(".platform-seg-btn");
        segBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                segBtns.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
            });
        });
    }

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

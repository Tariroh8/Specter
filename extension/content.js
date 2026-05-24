// Specter AI Chat Tracker - Content Script
// This script runs on chatgpt.com, claude.ai, and gemini.google.com

let lastSentContent = "";
let sourceName = "Unknown AI";

if (window.location.hostname.includes("chatgpt.com")) {
    sourceName = "ChatGPT";
} else if (window.location.hostname.includes("claude.ai")) {
    sourceName = "Claude";
} else if (window.location.hostname.includes("gemini.google.com") || window.location.hostname.includes("aistudio.google.com")) {
    sourceName = "Gemini";
}

function extractChatText() {
    let chatText = "";
    
    if (sourceName === "ChatGPT") {
        // ChatGPT typically uses article tags for messages
        const messages = document.querySelectorAll('article');
        if (messages.length > 0) {
            messages.forEach(msg => {
                const role = msg.getAttribute('data-message-author-role') || 'unknown';
                chatText += `[${role.toUpperCase()}]\n${msg.innerText}\n\n`;
            });
            return chatText.trim();
        }
        // Fallback
        const main = document.querySelector('main');
        if (main) return main.innerText;
    } 
    else if (sourceName === "Claude") {
        // Claude uses specific classes for user and claude messages
        const messages = document.querySelectorAll('.font-user-message, .font-claude-message');
        if (messages.length > 0) {
            messages.forEach(msg => {
                const role = msg.classList.contains('font-user-message') ? 'USER' : 'CLAUDE';
                chatText += `[${role}]\n${msg.innerText}\n\n`;
            });
            return chatText.trim();
        }
        // Fallback
        const main = document.querySelector('main');
        if (main) return main.innerText;
    }
    else if (sourceName === "Gemini") {
        // Gemini DOM is complex, extracting the main conversation
        const conversation = document.querySelector('chat-app') || document.querySelector('.conversation-container') || document.querySelector('main');
        if (conversation) {
            return conversation.innerText;
        }
    }
    
    return document.body.innerText;
}

function sendToSpecter(content) {
    fetch('http://127.0.0.1:5000/api/extension/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            source: sourceName,
            content: content
        })
    }).catch(err => {
        // Silent catch so it doesn't spam console if Specter server is off
        // console.error("[Specter] Failed to send chat data:", err);
    });
}

function checkAndSend() {
    const currentContent = extractChatText();
    if (currentContent && currentContent.trim().length > 0 && currentContent !== lastSentContent) {
        lastSentContent = currentContent;
        sendToSpecter(currentContent);
        // console.log(`[Specter] Sent updated ${sourceName} chat to local server. length: ${currentContent.length}`);
    }
}

// Check for updates every 5 seconds
setInterval(checkAndSend, 5000);

// Also check when user is likely to submit a prompt (enter key)
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        setTimeout(checkAndSend, 1000); // Wait a bit for UI to update
    }
});

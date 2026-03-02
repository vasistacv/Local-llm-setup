const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const apiKeyInput = document.getElementById('ui-api-key');
const imageUpload = document.getElementById('image-upload');
const imagePreviewContainer = document.getElementById('image-preview-container');
const imagePreview = document.getElementById('image-preview');

let currentImageB64 = null;

// Load API Key from LocalStorage
window.onload = () => {
    const savedKey = localStorage.getItem('college_api_key');
    if (savedKey) {
        apiKeyInput.value = savedKey;
    }
};

function saveApiKey() {
    localStorage.setItem('college_api_key', apiKeyInput.value);
}

function showKeyManager() {
    document.getElementById('chat-view').style.display = 'none';
    document.getElementById('key-view').style.display = 'flex';
}

function previewImage() {
    const file = imageUpload.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            imagePreview.src = e.target.result;
            currentImageB64 = e.target.result; // Data URL format
            imagePreviewContainer.style.display = 'flex';
        };
        reader.readAsDataURL(file);
    }
}

function clearImage() {
    currentImageB64 = null;
    imageUpload.value = '';
    imagePreviewContainer.style.display = 'none';
    imagePreview.src = '';
}

userInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const text = userInput.value.trim();
    const apiKey = apiKeyInput.value.trim();

    if (!text && !currentImageB64) return;
    if (!apiKey) {
        alert("Please enter an API Key in the sidebar.");
        return;
    }

    // Add User Message to UI
    appendMessage('user', text, currentImageB64);

    // Clear input
    userInput.value = '';
    const imgData = currentImageB64;
    clearImage(); // reset

    // Create Bot Message placeholder
    const botMsgId = 'msg-' + Date.now();
    appendMessage('bot', '', null, botMsgId);
    const botMsgContent = document.getElementById(botMsgId);

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': apiKey
            },
            body: JSON.stringify({
                message: text,
                image_b64: imgData
            })
        });

        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                botMsgContent.innerHTML = "<strong>Error:</strong> Invalid or Missing API Key.";
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let fullText = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            fullText += decoder.decode(value, { stream: true });
            botMsgContent.innerHTML = parseMarkdown(fullText);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    } catch (e) {
        botMsgContent.innerHTML = `<strong>Error:</strong> Could not connect to H200 Cluster. (${e.message})`;
    }
}

function appendMessage(sender, text, imageB64 = null, id = null) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}-msg`;

    let contentHtml = `<div class="msg-content" ${id ? `id="${id}"` : ''}>`;

    if (imageB64) {
        contentHtml += `<img src="${imageB64}" class="msg-image" style="max-width: 200px; border-radius: 8px; margin-bottom: 10px;">`;
    }

    contentHtml += `<span>${parseMarkdown(text)}</span></div>`;
    msgDiv.innerHTML = contentHtml;

    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Simple markdown parsing for the streams
function parseMarkdown(text) {
    return text
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

// --- Admin Panel Functions ---
async function generateKey() {
    const owner = document.getElementById('owner-name').value;
    const master = document.getElementById('master-key').value;

    if (!owner || !master) {
        alert("Fill both fields");
        return;
    }

    try {
        const res = await fetch('/api/admin/keys/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ owner_name: owner, admin_key: master })
        });

        const data = await res.json();
        const resultDiv = document.getElementById('new-key-result');
        if (res.ok) {
            resultDiv.innerHTML = `<div style="color: #10b981; margin-top: 15px;">
                <strong>Key Generated:</strong><br>
                <code style="background: #1e1e2d; padding: 10px; display: block; border-radius: 4px; margin: 10px 0; color: #fff;">${data.api_key}</code>
                Give this strictly to ${data.owner}.
            </div>`;
        } else {
            resultDiv.innerHTML = `<span style="color: #ef4444;">Error: ${data.detail}</span>`;
        }
    } catch (e) {
        alert("Server error.");
    }
}

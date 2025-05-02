// Global variables
let editor;
let socket;
let isEditorReady = false;
let lastSentContent = '';
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
const reconnectDelay = 3000;
let remoteCursors = {};
let remoteSelections = {};
let isTyping = false;
let typingTimeout;

// Get project and file IDs from the container
const container = document.getElementById('editor-container');
const projectId = container.dataset.projectId;
const fileId = container.dataset.fileId;
const language = container.dataset.language;

// Get initial content
const initialContent = document.getElementById('initial-content').textContent;

// Initialize Monaco Editor
function initializeEditor() {
    if (!window.monaco) {
        console.error('Monaco Editor not loaded');
        return;
    }

    // Get initial content and decode HTML entities
    const initialContent = document.getElementById('initial-content').textContent
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&amp;/g, '&')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'");

    editor = monaco.editor.create(document.getElementById('editor'), {
        value: initialContent,
        language: language,
        theme: 'vs-dark',
        automaticLayout: true,
        minimap: {
            enabled: true
        },
        fontSize: 14,
        fontFamily: "'Fira Code', monospace",
        lineNumbers: 'on',
        roundedSelection: false,
        scrollBeyondLastLine: false,
        readOnly: false,
        cursorStyle: 'line',
        cursorBlinking: 'blink',
        tabSize: 4,
        insertSpaces: true,
        wordWrap: 'on',
        folding: true,
        lineDecorationsWidth: 0,
        lineNumbersMinChars: 3,
        renderLineHighlight: 'all',
        scrollbar: {
            vertical: 'visible',
            horizontal: 'visible'
        }
    });

    // Set up editor event listeners
    editor.onDidChangeModelContent(() => {
        if (!isTyping) {
            isTyping = true;
            showInfoNotification('You are now typing...');
        }
        
        clearTimeout(typingTimeout);
        typingTimeout = setTimeout(() => {
            isTyping = false;
            sendCodeChanges();
        }, 1000);
    });

    editor.onDidChangeCursorPosition((e) => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            const position = editor.getPosition();
            socket.send(JSON.stringify({
                type: 'cursor_update',
                position: {
                    lineNumber: position.lineNumber,
                    column: position.column
                }
            }));
        }
    });

    // Handle window resize
    window.addEventListener('resize', () => {
        editor.layout();
    });

    isEditorReady = true;
    lastSentContent = editor.getValue();
    initializeWebSocket();
}

// Initialize WebSocket connection
function initializeWebSocket() {
    // Set up the WebSocket connection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/projects/${projectId}/files/${fileId}/`;
    
    console.log('WebSocket Connection Details:');
    console.log('Protocol:', protocol);
    console.log('Host:', window.location.host);
    console.log('Project ID:', projectId);
    console.log('File ID:', fileId);
    console.log('Full WebSocket URL:', wsUrl);
    console.log('User Authentication Status:', document.cookie.includes('sessionid') ? 'Authenticated' : 'Not Authenticated');
    
    try {
        socket = new WebSocket(wsUrl);
        
        // Set a connection timeout
        const connectionTimeout = setTimeout(() => {
            if (socket.readyState !== WebSocket.OPEN) {
                console.error('WebSocket connection timeout');
                socket.close();
            }
        }, 5000);
        
        socket.onopen = () => {
            console.log('WebSocket connection established successfully');
            clearTimeout(connectionTimeout);
            showSuccessNotification('Connected to collaboration server');
            
            reconnectAttempts = 0;
            // Send any pending changes
            if (isEditorReady && editor.getValue() !== lastSentContent) {
                sendCodeChanges();
            }
        };
        
        socket.onmessage = (event) => {
            console.log('Received WebSocket message:', event.data);
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        socket.onclose = (event) => {
            console.log('WebSocket connection closed:', event.code, event.reason);
            
            // Auto-save when connection is lost
            if (isEditorReady && editor.getValue() !== lastSentContent) {
                console.log('Auto-saving content after connection loss...');
                saveContent(editor.getValue());
            }
            
            let errorMessage = 'Connection lost. ';
            switch (event.code) {
                case 4001:
                    errorMessage += 'Authentication required. Please log in again.';
                    break;
                case 4003:
                    errorMessage += 'Access denied. You do not have permission to access this file.';
                    break;
                case 1011:
                    errorMessage += `Server error: ${event.reason}`;
                    break;
                case 1006:
                    errorMessage += 'Connection failed. Please check if the server is running with Daphne.';
                    break;
                default:
                    errorMessage += 'Please refresh the page to try again.';
            }
            
            if (reconnectAttempts < maxReconnectAttempts) {
                setTimeout(() => {
                    console.log(`Attempting to reconnect (${reconnectAttempts + 1}/${maxReconnectAttempts})...`);
                    showInfoNotification(`Reconnecting... (${reconnectAttempts + 1}/${maxReconnectAttempts})`);
                    reconnectAttempts++;
                    initializeWebSocket();
                }, reconnectDelay);
            } else {
                console.error('Maximum reconnection attempts reached. Please refresh the page.');
                showErrorNotification(errorMessage);
                
                // Add connection error message to editor
                if (isEditorReady) {
                    const errorMsg = document.createElement('div');
                    errorMsg.className = 'absolute top-0 left-0 w-full bg-red-100 text-red-800 p-4 flex justify-between items-center';
                    errorMsg.style = 'z-index: 1000; border-bottom: 1px solid #f5c6cb;';
                    errorMsg.innerHTML = `
                        <div>
                            <strong>Connection Error:</strong> ${errorMessage}
                        </div>
                        <button onclick="window.location.reload()" class="px-3 py-1 bg-red-700 text-white rounded hover:bg-red-800">
                            Refresh Page
                        </button>
                    `;
                    document.querySelector('#editor-container').prepend(errorMsg);
                }
            }
        };
        
        socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            // Log additional error details if available
            if (error.message) {
                console.error('Error message:', error.message);
            }
            if (error.type) {
                console.error('Error type:', error.type);
            }
        };
    } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        showErrorNotification('Failed to create collaboration connection. Please refresh the page.');
    }
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'code_update':
            handleCodeUpdate(data);
            break;
        case 'cursor_update':
            handleCursorUpdate(data);
            break;
        case 'user_joined':
            handleUserJoined(data);
            break;
        case 'user_left':
            handleUserLeft(data);
            break;
        case 'error':
            showErrorNotification(data.message);
            break;
        default:
            console.warn('Unknown message type:', data.type);
    }
}

// Handle code updates from other users
function handleCodeUpdate(data) {
    if (!isEditorReady || data.user === getCurrentUsername()) return;
    
    const currentPosition = editor.getPosition();
    const currentScroll = editor.getScrollPosition();
    
    editor.setValue(data.content);
    
    // Restore cursor position and scroll
    editor.setPosition(currentPosition);
    editor.setScrollPosition(currentScroll);
    
    lastSentContent = data.content;
}

// Handle cursor updates from other users
function handleCursorUpdate(data) {
    if (!isEditorReady || data.user === getCurrentUsername()) return;
    
    const position = data.position;
    updateRemoteCursor(data.user, position);
}

// Update remote cursor position
function updateRemoteCursor(username, position) {
    // Remove existing cursor if any
    removeRemoteCursor(username);
    
    // Create new cursor
    const cursor = document.createElement('div');
    cursor.className = 'remote-cursor';
    cursor.style.backgroundColor = getCursorColor(username);
    
    const label = document.createElement('div');
    label.className = 'remote-cursor-label';
    label.style.backgroundColor = getCursorColor(username);
    label.textContent = username;
    
    // Position cursor and label
    const coords = editor.getScrolledVisiblePosition({
        lineNumber: position.lineNumber,
        column: position.column
    });
    
    cursor.style.left = coords.left + 'px';
    cursor.style.top = coords.top + 'px';
    
    label.style.left = coords.left + 'px';
    label.style.top = (coords.top - 20) + 'px';
    
    // Add to DOM
    const container = editor.getContainerDomNode();
    container.appendChild(cursor);
    container.appendChild(label);
    
    // Store references
    remoteCursors[username] = { cursor, label };
}

// Remove remote cursor
function removeRemoteCursor(username) {
    if (remoteCursors[username]) {
        remoteCursors[username].cursor.remove();
        remoteCursors[username].label.remove();
        delete remoteCursors[username];
    }
}

// Handle user joined event
function handleUserJoined(data) {
    showInfoNotification(`${data.username} joined the session`);
}

// Handle user left event
function handleUserLeft(data) {
    showInfoNotification(`${data.username} left the session`);
    removeRemoteCursor(data.username);
}

// Send code changes to server
function sendCodeChanges() {
    if (!isEditorReady || !socket || socket.readyState !== WebSocket.OPEN) {
        console.log('Cannot send code changes: Editor not ready or socket not connected');
        return;
    }
    
    const content = editor.getValue();
    if (content === lastSentContent) {
        console.log('No changes to send');
        return;
    }
    
    console.log('Sending code changes...');
    socket.send(JSON.stringify({
        type: 'code_update',
        content: content
    }));
    
    lastSentContent = content;
}

// Get current username from meta tag
function getCurrentUsername() {
    const metaTag = document.querySelector('meta[name="username"]');
    return metaTag ? metaTag.content : null;
}

// Get cursor color for user
function getCursorColor(username) {
    const colors = [
        '#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff',
        '#00ffff', '#ff8000', '#8000ff', '#00ff80', '#ff0080'
    ];
    
    let hash = 0;
    for (let i = 0; i < username.length; i++) {
        hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    return colors[Math.abs(hash) % colors.length];
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Trigger reflow
    notification.offsetHeight;
    
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function showSuccessNotification(message) {
    showNotification(message, 'success');
}

function showErrorNotification(message) {
    showNotification(message, 'error');
}

function showInfoNotification(message) {
    showNotification(message, 'info');
}

// Save content function
async function saveContent(content) {
    try {
        const projectId = document.getElementById('editor-container').dataset.projectId;
        const fileId = document.getElementById('editor-container').dataset.fileId;
        
        console.log('Saving content to server...');
        const response = await fetch(`/projects/${projectId}/files/${fileId}/save/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ content })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to save file');
        }
        
        lastSentContent = content;
        return true;
    } catch (error) {
        console.error('Save error:', error);
        showErrorNotification(error.message || 'Failed to save file');
        return false;
    }
}

// Save button handler
document.getElementById('save-btn').addEventListener('click', async () => {
    if (!isEditorReady) return;
    
    const content = editor.getValue();
    const success = await saveContent(content);
    
    if (success) {
        showSuccessNotification('File saved successfully');
    }
});

// Add auto-save on window unload
window.addEventListener('beforeunload', async (event) => {
    if (isEditorReady && editor.getValue() !== lastSentContent) {
        event.preventDefault();
        event.returnValue = '';
        
        // Try to save before leaving
        const success = await saveContent(editor.getValue());
        if (success) {
            showSuccessNotification('Changes saved before leaving');
        }
    }
});

// Initialize editor when Monaco is loaded
if (window.monaco) {
    initializeEditor();
} else {
    window.addEventListener('monaco-loaded', initializeEditor);
}

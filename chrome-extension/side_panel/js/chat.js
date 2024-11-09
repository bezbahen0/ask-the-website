import { ContentManager } from './contentManager.js';

export class Chat {
    constructor({ settings, context, onMessageSend }) {
        this.settings = settings;
        this.context = context;
        this.onMessageSend = onMessageSend;
        this.isStreaming = false;
        this.currentStreamingDiv = null;
        this.initElements();
        this.bindEvents();
    }

    initElements() {
        this.resultDiv = document.getElementById('result');
        this.queryInput = document.getElementById('queryInput');
        this.submitButton = document.getElementById('submitButton');
        this.clearConvo = document.getElementById('ClearConvo');
    }

    bindEvents() {
        this.submitButton.addEventListener('click', () => this.handleSubmit());
        this.queryInput.addEventListener('keyup', (e) => this.handleKeyPress(e));
        this.clearConvo.addEventListener('click', () => this.clearChat());
        this.resultDiv.addEventListener('click', (e) => this.handleResultClick(e));
    }

    async handleSubmit() {
        const query = this.queryInput.value;
        if (!query.trim()) return;

        const chatId = localStorage.getItem("chat_id");
        const contextParams = this.context.getContextParams();
        
        this.displayMessage(query, 'user');
        this.displayLoading();
        
        try {
            await this.onMessageSend({ query, chatId, contextParams });
            this.queryInput.value = '';
        } catch (error) {
            this.displayError('Failed to send message');
            console.error('Error in handleSubmit:', error);
        }
    }

    handleKeyPress(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            if (this.queryInput.value.trim()) {
                this.handleSubmit();
            }
        }
    }

    handleResultClick(event) {
        if (event.target.id === 'copyCode') {
            const codeDiv = event.target.parentNode;
            const codeText = codeDiv.querySelector('pre').textContent;
            this.copyToClipboard(codeText);
        }
    }

    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            console.log('Code copied to clipboard');
        } catch (err) {
            console.error('Failed to copy code:', err);
        }
    }

    displayMessage(text, type) {
        const processedText = ContentManager.processMessage(text);
        const messageDiv = document.createElement('div');
        messageDiv.className = type;
        messageDiv.innerHTML = `${type === 'user' ? 'You: ' : 'Response: '}${processedText}`;
        this.resultDiv.appendChild(messageDiv);
        this.scrollToBottom();
    }

    displayLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        loadingDiv.textContent = 'Llama is thinking...';
        this.resultDiv.appendChild(loadingDiv);
        this.scrollToBottom();
    }

    removeLoading() {
        const loadingDiv = this.resultDiv.querySelector('.loading');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    displayError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.textContent = message;
        this.resultDiv.appendChild(errorDiv);
        this.scrollToBottom();
    }

    updateStreamingResponse(text, isComplete = false) {
        this.removeLoading();
        
        if (!this.currentStreamingDiv) {
            this.currentStreamingDiv = document.createElement('div');
            this.currentStreamingDiv.className = 'bot';
            this.resultDiv.appendChild(this.currentStreamingDiv);
        }

        const processedText = ContentManager.processMessage(text);
        this.currentStreamingDiv.innerHTML = `Response: ${processedText}`;
        this.scrollToBottom();

        if (isComplete) {
            this.finalizeStreamingResponse();
        }
    }

    finalizeStreamingResponse() {
        if (this.currentStreamingDiv) {
            this.currentStreamingDiv.className = 'bot';
            this.currentStreamingDiv = null;
        }
    }

    async clearChat() {
        this.resultDiv.innerHTML = '';
        
        try {
            const response = await fetch(`${this.settings.url}get_chat_id`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                mode: 'cors',
            });

            const data = await response.json();
            if (data.new_chat_id) {
                localStorage.setItem('chat_id', data.new_chat_id);
            }
        } catch (error) {
            console.error('Error getting new chat ID:', error);
            this.displayError('Failed to reset chat');
        }
    }

    async loadSavedMessages() {
        const chatId = localStorage.getItem('chat_id');
        if (!chatId) {
            await this.getNewChatId();
            return;
        }

        try {
            const messages = await this.getMessages(chatId);
            if (messages) {
                this.displaySavedMessages(messages);
            }
        } catch (error) {
            console.error('Error loading saved messages:', error);
        }
    }

    async getNewChatId() {
        try {
            const response = await fetch(`${this.settings.url}get_chat_id`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                mode: 'cors',
            });

            const data = await response.json();
            if (data.new_chat_id) {
                localStorage.setItem('chat_id', data.new_chat_id);
            }
        } catch (error) {
            console.error('Error getting new chat ID:', error);
        }
    }

    async getMessages(chatId) {
        try {
            const response = await fetch(`${this.settings.url}get_chat_messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ chat_id: chatId })
            });

            const data = await response.json();
            return data.dialog;
        } catch (error) {
            console.error('Error getting messages:', error);
            return null;
        }
    }

    displaySavedMessages(messages) {
        messages.forEach(entry => {
            if ("user" in entry) {
                this.displayMessage(entry.user, 'user');
            } else if ("bot" in entry) {
                this.displayMessage(entry.bot, 'bot');
            }
        });
    }

    scrollToBottom() {
        this.resultDiv.scrollTop = this.resultDiv.scrollHeight;
    }

    updateSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
    }

    updateContext(newContext) {
        this.context = { ...this.context, ...newContext };
    }
}
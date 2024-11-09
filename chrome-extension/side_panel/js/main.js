import { Settings } from './settings.js';
import { Chat } from './chat.js';
import { Context } from './context.js';
import { Inspector } from './inspector.js';
import { ContentManager } from './contentManager.js';

class App {
    constructor() {
        this.initializeComponents();
        this.state = {
            currentModel: null,
            isInspectorActive: false,
            selectedContent: null,
            contextSettings: null
        };
    }

    initializeComponents() {
        this.settings = new Settings({
            onSettingsChange: this.handleSettingsChange.bind(this)
        });

        this.context = new Context({
            onContextChange: this.handleContextChange.bind(this)
        });

        this.inspector = new Inspector({
            onSelectionChange: this.handleInspectorSelection.bind(this)
        });

        this.chat = new Chat({
            settings: this.settings,
            context: this.context,
            onMessageSend: this.handleMessageSend.bind(this)
        });
    }

    handleSettingsChange(newSettings) {
        this.state.currentModel = newSettings.model;
        console.log('Settings updated:', newSettings);
    }

    handleContextChange(newContext) {
        this.state.contextSettings = newContext;
        console.log('Context updated:', newContext);
    }

    handleInspectorSelection(selectedContent) {
        this.state.selectedContent = selectedContent;
        console.log('Selection updated:', selectedContent);
    }

    async handleMessageSend({ query, chatId, contextParams }) {
        try {
            const pageContent = this.state.selectedContent || await ContentManager.getPageContent();
            const response = await this.sendRequest({
                query,
                chatId,
                pageUrl: pageContent.url,
                pageContent: pageContent.content,
                contextParams
            });
            this.chat.displayMessage(response, 'bot');
        } catch (error) {
            console.error('Error sending message:', error);
            this.chat.displayError('Failed to send message');
        }
    }

    async sendRequest({ query, chatId, pageUrl, pageContent, contextParams }) {
        const url = `${this.settings.url}query`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query,
                chat_id: chatId,
                page_url: pageUrl,
                page_content: pageContent,
                processing_settings: contextParams
            }),
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        return this.handleStreamResponse(response);
    }

    async handleStreamResponse(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let accumulatedResponse = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            accumulatedResponse += chunk;
            this.chat.updateStreamingResponse(accumulatedResponse);
        }

        return accumulatedResponse;
    }

    async initialize() {
        try {
            await this.settings.loadInitialSettings();
            const serverStatus = await this.settings.checkServer();
            if (!serverStatus) {
                console.warn('Server is not responding');
            }
            await this.chat.loadSavedMessages();
            console.log('App initialized successfully');
        } catch (error) {
            console.error('Failed to initialize app:', error);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.initialize().catch(error => {
        console.error('Failed to initialize app:', error);
    });
});
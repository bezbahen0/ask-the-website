export class Settings {
    constructor({ onSettingsChange }) {
        this.ip = '127.0.0.1';
        this.port = '8080';
        this.url = `http://${this.ip}:${this.port}/`;
        this.onSettingsChange = onSettingsChange;
        this.initElements();
        this.bindEvents();
    }

    initElements() {
        this.serverIP = document.getElementById('serverIP');
        this.serverPort = document.getElementById('serverPort');
        this.settingsButton = document.getElementById('settingMenuBtn');
        this.settingsWindow = document.getElementById('settings-wrapper');
        this.settingsClose = document.getElementById('settingsClose');
        this.modelSelect = document.getElementById('modelSelect');
        this.changeModelButton = document.getElementById('changeModel');
        this.serverCheckButton = document.getElementById('serverCheck');
        this.modelLoadedElement = document.getElementById('modelLoaded');
    }

    bindEvents() {
        this.serverIP.addEventListener('change', () => this.updateIP());
        this.serverPort.addEventListener('change', () => this.updatePort());
        this.settingsButton.addEventListener('click', () => this.toggleSettings());
        this.settingsClose.addEventListener('click', () => this.closeSettings());
        this.changeModelButton.addEventListener('click', () => this.changeModel());
        this.serverCheckButton.addEventListener('click', () => this.checkServer());
    }

    updateIP() {
        this.ip = this.serverIP.value;
        this.updateUrl();
    }

    updatePort() {
        this.port = this.serverPort.value;
        this.updateUrl();
    }

    updateUrl() {
        this.url = `http://${this.ip}:${this.port}/`;
        this.onSettingsChange({ 
            ip: this.ip, 
            port: this.port, 
            url: this.url 
        });
    }

    toggleSettings() {
        if (this.settingsWindow.style.display === 'block') {
            this.closeSettings();
        } else {
            this.openSettings();
        }
    }

    async openSettings() {
        this.settingsWindow.style.display = 'block';
        this.setIPAndPortValues();
        await this.getCurrentModel();
        await this.getAvailableModels();
    }

    closeSettings() {
        this.settingsWindow.style.display = 'none';
    }

    setIPAndPortValues() {
        this.serverIP.value = this.ip;
        this.serverPort.value = this.port;
    }

    async checkServer() {
        try {
            const response = await fetch(`${this.url}health`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                mode: 'cors',
            });
            
            if (response.ok) {
                this.serverCheckButton.style.backgroundColor = 'green';
                return true;
            } else {
                throw new Error('Server response not ok');
            }
        } catch (error) {
            console.error('Server check failed:', error);
            this.serverCheckButton.style.backgroundColor = 'red';
            return false;
        }
    }

    async getCurrentModel() {
        try {
            const response = await fetch(`${this.url}get_current_model`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                mode: 'cors',
            });

            const data = await response.json();
            if (data.current_model) {
                this.modelLoadedElement.innerText = data.current_model;
                this.onSettingsChange({ currentModel: data.current_model });
            }
        } catch (error) {
            console.error('Error getting current model:', error);
            this.modelLoadedElement.innerText = 'Error loading model info';
        }
    }

    async getAvailableModels() {
        try {
            const response = await fetch(`${this.url}get_gguf_files`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                mode: 'cors',
            });

            const data = await response.json();
            if (data.gguf_files && data.gguf_files.length) {
                this.updateModelSelect(data.gguf_files);
            }
        } catch (error) {
            console.error('Error getting available models:', error);
        }
    }

    updateModelSelect(models) {
        this.modelSelect.innerHTML = '';

        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            this.modelSelect.appendChild(option);
        });
    }

    async changeModel() {
        const selectedModel = this.modelSelect.value;
        if (!selectedModel) return;

        try {
            const response = await fetch(`${this.url}load_model`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                mode: 'cors',
                body: JSON.stringify({ model: selectedModel }),
            });

            const data = await response.json();
            if (data.current_model) {
                this.modelLoadedElement.innerText = data.current_model;
                this.onSettingsChange({ currentModel: data.current_model });
            }
        } catch (error) {
            console.error('Error changing model:', error);
            this.modelLoadedElement.innerText = 'Error changing model';
        }
    }

    async loadInitialSettings() {
        const savedIP = localStorage.getItem('serverIP');
        const savedPort = localStorage.getItem('serverPort');

        if (savedIP) this.ip = savedIP;
        if (savedPort) this.port = savedPort;

        this.setIPAndPortValues();
        this.updateUrl();
        
        await this.getCurrentModel();
    }

    saveSettings() {
        localStorage.setItem('serverIP', this.ip);
        localStorage.setItem('serverPort', this.port);
    }

    getSettings() {
        return {
            ip: this.ip,
            port: this.port,
            url: this.url,
            currentModel: this.modelLoadedElement.innerText
        };
    }
}
export class Inspector {
    constructor({ onSelectionChange }) {
        this.onSelectionChange = onSelectionChange;
        this.initElements();
        this.bindEvents();
    }

    initElements() {
        this.selectTagButton = document.getElementById('selectTagButton');
    }

    bindEvents() {
        this.selectTagButton.addEventListener('click', () => this.toggleInspector());
        this.setupChromeListeners();
    }

    setupChromeListeners() {
        chrome.tabs.onActivated.addListener((activeInfo) => {
            chrome.tabs.get(activeInfo.tabId, () => this.checkInspectorStatus());
        });

        chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
            if (changeInfo.status === 'complete') {
                this.checkInspectorStatus();
            }
        });
    }

    toggleInspector() {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, { action: "inspectorTrigger" }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error(chrome.runtime.lastError.message);
                    return;
                }
                this.updateButtonState(response.status);
            });
        });
    }

    checkInspectorStatus() {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, { action: "isInspectorActive" }, (response) => {
                if (chrome.runtime.lastError) {
                    this.updateButtonState(false);
                    return;
                }
                this.updateButtonState(response.status);
            });
        });
    }

    updateButtonState(isActive) {
        this.selectTagButton.classList.toggle('active', isActive);
    }
}
const contextConfigs = {
    'text/html': [
        { backend_id: 'use_tag_attributes', id: 'useTagAttributes', label: 'Tag Attributes' },
        { backend_id: 'use_only_text', id: 'useOnlyText', label: 'Only text' },
        { backend_id: 'body', id: 'useBodyTag', label: 'Body' },
        { backend_id: 'head', id: 'useHeadTag', label: 'Head' },
        { backend_id: 'script', id: 'useScriptTag', label: 'Scripts' }
    ],
 };


export class Context {
    constructor({ onContextChange }) {
        this.useContext = false;
        this.onContextChange = onContextChange;
        this.contentType = "text/html";
        this.initElements();
        this.bindEvents();
    }

    initElements() {
        this.usePageContext = document.getElementById('usePageContext');
        this.contextOptions = document.getElementById('contextOptions');
    }

    bindEvents() {
        this.usePageContext.addEventListener('change', () => this.toggleContext());

        this.setupChromeListeners();
    }

    setupChromeListeners() {
        chrome.tabs.onActivated.addListener((activeInfo) => {
            chrome.tabs.get(activeInfo.tabId, () => {
                this.updateContextOptions().catch(console.error);
            });
        });
    
        chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
            if (changeInfo.status === 'complete') {
                this.updateContextOptions().catch(console.error);
            }
        });
    }

    async updateContextOptions() {
        this.contentType = await this.getPageContentType();
        this.generateContextOptions(this.contentType);
    }

    async getPageContentType() {
        return new Promise((resolve) => {
            chrome.tabs.query({active: true, currentWindow: true}, async function(tabs) {
                let currentTab = tabs[0];
                
                if (currentTab.url.startsWith('chrome://')) {
                    resolve("");
                    return;
                }

                try {
                    
                    let response = await fetch(currentTab.url);
                    let contentType = response.headers.get('Content-Type');
                    contentType = contentType.split(';')[0];
                    console.log('Content Type:', contentType);
                    resolve(contentType);
                } catch(error) {
                    resolve("");
                }
            });
        });
    }

    generateContextOptions(contentType) {
        this.contextOptions.innerHTML = '';
        console.log('Generating options for content type:', contentType);
        const options = contextConfigs[contentType] || [];
        console.log('Available options:', options);
    
        options.forEach(option => {
            const label = document.createElement('label');
            const input = document.createElement('input');
            
            input.type = 'checkbox';
            input.id = option.id;
            
            label.appendChild(input);
            label.appendChild(document.createTextNode(option.label));
            
            this.contextOptions.appendChild(label);
        });
    }

    async toggleContext() {
        this.contextOptions.style.display = this.usePageContext.checked ? 'block' : 'none';
        this.useContext = this.usePageContext.checked;
    
        await this.updateContextOptions();
    
        this.generateContextOptions(this.contentType);
    
        this.onContextChange(this.getContextParams());
    }

    getContextParams() {

        const options = contextConfigs[this.contentType] || [];

        let contextParams = {};
        
        options.forEach(option => {
  
            const element = document.getElementById(option.id);
            contextParams[option.backend_id] = element.checked
        });

        console.log(contextParams)

        return {use_page_context: this.usePageContext.checked, content_type: this.contentType, processing_settings: contextParams};
    }
}
export class Context {
    constructor({ onContextChange }) {
        this.useContext = false;
        this.onContextChange = onContextChange;
        this.initElements();
        this.bindEvents();
    }

    initElements() {
        this.usePageContext = document.getElementById('usePageContext');
        this.contextOptions = document.getElementById('contextOptions');
        this.useTagAttributes = document.getElementById('useTagAttributes');
        this.useBodyTag = document.getElementById('useBodyTag');
        this.useHeadTag = document.getElementById('useHeadTag');
        this.useScriptTag = document.getElementById('useScriptTag');
    }

    bindEvents() {
        this.usePageContext.addEventListener('change', () => this.toggleContext());
    }

    toggleContext() {
        this.contextOptions.style.display = this.usePageContext.checked ? 'block' : 'none';
        this.useContext = this.usePageContext.checked;
        this.onContextChange(this.getContextParams());
    }

    getContextParams() {
        return {
            use_page_context: this.useContext,
            tag_attributes: this.useTagAttributes.checked,
            body: this.useBodyTag.checked,
            head: this.useHeadTag.checked,
            scripts: this.useScriptTag.checked,
        };
    }
}
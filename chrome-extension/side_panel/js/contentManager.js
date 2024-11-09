export class ContentManager {
    static processMessage(text) {
        text = text.replace(/(?:\r\n|\r|\n)/g, '<br>');
        text = text.replace(/\. \*/g, '\n');
        text = text.replace(/\. \d/g, '\n');

        const codeResponse = text.match(/```(.*?)```/g);
        if (codeResponse) {
            text = text.replace(/```<br>/g, '```');
            text = text.replace(/```python/g, '```');
            text = text.replace(/```javascript/g, '```');
            text = text.replace(/```(.*?)```/g, '<div class="code"><pre>$1</pre><div id="copyCode">copy</div></div>');
        }
        return text;
    }

    static getPageContent() {
        return new Promise((resolve) => {
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                if (chrome.runtime.lastError) {
                    resolve({ url: "", content: "" });
                    return;
                }

                const tabId = tabs[0].id;
                const tabUrl = tabs[0].url;

                chrome.tabs.sendMessage(tabId, { action: "getPageContent" }, (response) => {
                    if (chrome.runtime.lastError) {
                        resolve({ url: tabUrl, content: "" });
                        return;
                    }
                    resolve({ url: tabUrl, content: response ? response.content : "" });
                });
            });
        });
    }
}
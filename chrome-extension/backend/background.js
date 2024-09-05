chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: "inspectElement",
        title: "Inspect Element",
        contexts: ["all"]
    });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "inspectElement") {
        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ["backend/inspect.js"]
        });
    }
});
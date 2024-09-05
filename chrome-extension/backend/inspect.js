let inspectorStatus = false;
let selectedHTML = "";

// Popup Setup
const inspector_selector = (() => {
    const element = document.createElement('span');
    element.id = 'inspector_selector';
    element.className = 'hidden';
    document.body.appendChild(element);
    return element;
})();

const highlight = (target) => {
    target.classList.add('highlighted');
    inspector_selector.classList.remove('hidden');

    const rect = target.getBoundingClientRect();
    inspector_selector.style.top = `${rect.top + window.scrollY + rect.height + 5}px`;
    inspector_selector.style.left = `${rect.left + window.scrollX}px`;

    // Attach the click handler
    target.addEventListener('click', inspectorTargetClickHandler);
};

const removeHighlight = (target) => {
    target.classList.remove('highlighted');
    inspector_selector.classList.add('hidden');
    target.removeEventListener('click', inspectorTargetClickHandler);
};

const inspectorTargetClickHandler = (event) => {
    event.preventDefault();
    event.stopImmediatePropagation();

    selectedHTML = event.target.outerHTML;
    console.log('Selected element HTML:', selectedHTML); // Debugging log

    // Store the outerHTML in chrome.storage
    //chrome.storage.local.set({"selectedHTML": selectedHTML }, () => {
    //    console.log('Selected HTML has been stored.');
    //});

    removeHighlight(event.target);
    deactivateInspector(); // Deactivate inspector after selection
};

const inspectorHandler = (event) => {
    event.preventDefault();
    event.stopPropagation();

    if (event.target) {
        highlight(event.target);
        event.target.addEventListener('mouseout', inspectorMouseLeaveHandler, { once: true });
    }
};

const inspectorMouseLeaveHandler = (event) => {
    event.preventDefault();
    event.stopPropagation();
    removeHighlight(event.target);
};

// Inspector activation/deactivation
const activateInspector = () => {
    console.log('Inspector activated.'); // Debugging log
    inspectorStatus = true;
    document.addEventListener('mousemove', inspectorHandler);
};

const deactivateInspector = () => {
    console.log('Inspector deactivated.'); // Debugging log
    inspectorStatus = false;
    document.removeEventListener('mousemove', inspectorHandler);
};

const cleanInspector = () => {
    selectedHTML = "";  // Clear selected HTML on deactivation
    //chrome.storage.local.remove('selectedHTML', () => {
    //    console.log('Selected HTML cleared from chrome.storage.');
    //});
};

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "inspectorTrigger") {
        if (inspectorStatus) {
            deactivateInspector();  // Deactivate if it's already active
            sendResponse({ status: false });
        } else {
            activateInspector();  // Activate if it's not active
            sendResponse({ status: true });
        }
    } else if (message.action === "getSelectedHMTL") {
        sendResponse({ selected: selectedHTML });
    } else if (message.action === "isInspectorActive") {
        if (selectedHTML !== ""){
            sendResponse({ status: true });
        }
        else {
            sendResponse({ status: inspectorStatus });
        }
    }
});
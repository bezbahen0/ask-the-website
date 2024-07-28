chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === "getPageContent") {
        sendResponse({ content: document.documentElement.outerHTML });
    }
});


//chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
//    if (request.action === "getPageContent") {
//        let contentType = document.contentType || 'text/html';
//        let content;
//
//        if (contentType.includes('text/html')) {
//            content = document.documentElement.outerHTML;
//        } else if (contentType.includes('application/pdf')) {
//            // For PDFs, you might not be able to access the content directly
//            content = "PDF content - unable to access directly";
//        } else if (contentType.includes('image/')) {
//            // For images, you could potentially get the image source
//            content = document.images.length > 0 ? document.images[0].src : "No image found";
//        } else {
//            // For other types, you might need to use different methods or APIs
//            content = "Unsupported content type: " + contentType;
//        }
//
//        sendResponse({ content: content, contentType: contentType });
//    }
//});
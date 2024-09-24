chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === "getPageContent") {
        sendResponse({ content: document.documentElement.outerHTML });
    }
});



//chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
//    if (request.action === "getPageContent") {
//        // Базовая информация о странице
//        let pageInfo = {
//            url: window.location.href,
//            title: document.title,
//            html: document.documentElement.outerHTML,
//            viewport: {
//                width: window.innerWidth,
//                height: window.innerHeight
//            }
//        };
//
//        // Информация о всех элементах на странице
//        let elements = [];
//        document.querySelectorAll('*').forEach((el, index) => {
//            let rect = el.getBoundingClientRect();
//            let styles = window.getComputedStyle(el);
//            
//            elements.push({
//                tagName: el.tagName,
//                id: el.id,
//                classes: Array.from(el.classList),
//                text: el.textContent.trim(),
//                attributes: Array.from(el.attributes).map(attr => ({ name: attr.name, value: attr.value })),
//                rect: {
//                    top: rect.top,
//                    right: rect.right,
//                    bottom: rect.bottom,
//                    left: rect.left,
//                    width: rect.width,
//                    height: rect.height
//                },
//                styles: {
//                    display: styles.display,
//                    position: styles.position,
//                    zIndex: styles.zIndex,
//                    visibility: styles.visibility,
//                    opacity: styles.opacity,
//                    backgroundColor: styles.backgroundColor,
//                    color: styles.color,
//                    fontSize: styles.fontSize,
//                    fontWeight: styles.fontWeight
//                },
//                isVisible: isElementVisible(el)
//            });
//        });
//
//        // Добавляем информацию о элементах в pageInfo
//        pageInfo.elements = elements;
//
//        // Информация о ресурсах
//        let resources = performance.getEntriesByType("resource").map(r => ({
//            name: r.name,
//            entryType: r.entryType,
//            startTime: r.startTime,
//            duration: r.duration
//        }));
//        pageInfo.resources = resources;
//
//        // Отправляем собранную информацию
//        sendResponse({ pageInfo: pageInfo });
//    }
//});
//
//// Функция для проверки видимости элемента
//function isElementVisible(el) {
//    let style = window.getComputedStyle(el);
//    return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
//}


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
from server.partition.html_processor import HTMLProcessor

def get_processor(page_type="text/html"):
    if page_type == "text/html":
        processor = HTMLProcessor()
    else:
        raise NotImplementedError(f"page processor with content type '{page_type}' not supported")
    return processor
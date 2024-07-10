import html2text
from langchain_text_splitters import MarkdownHeaderTextSplitter


class HTMLProcessor:
    def __init__(self):
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_images = True
        self.html2text.ignore_links = True
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
            ("#####", "Header 5"),
        ]
        self.text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=self.headers_to_split_on)
        
    def to_md(self, html_content):
        return self.html2text.handle(html_content)

    def process_page(self, html_content):
        content_md = self.html2text.handle(html_content)
        chunks = self.text_splitter.split_text(content_md)
        return [c.page_content for c in chunks]

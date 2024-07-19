import html2text
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter


class HTMLProcessor:
    def __init__(self):
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_images = True
        # self.html2text.ignore_links = True

        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]

        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on, strip_headers=False
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len,
            is_separator_regex=False,
        )

    def to_md(self, html_content):
        return self.html2text.handle(html_content)

    def process_page(self, html_content, page_url):
        content_md = self.html2text.handle(html_content)
        md_header_splits = self.markdown_splitter.split_text(content_md)
        chunks = self.text_splitter.split_documents(md_header_splits)
        for idx, _ in enumerate(chunks):
            chunks[idx].metadata['source'] = page_url
        return chunks

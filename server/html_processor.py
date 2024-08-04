import html2text
from langchain_core.documents import Document
from bs4 import BeautifulSoup, NavigableString, Tag, Comment

from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)


class HTMLProcessor:
    def __init__(self, chunk_size=256, chunk_overlap=40, unicode=False):
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_images = True
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.unicode = unicode

        self.splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.MARKDOWN,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def assign_ids(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        id_counter = 1

        for tag in soup.find_all():
            if not tag.get("id"):
                tag["id"] = f"auto-id-{id_counter}"
                id_counter += 1

        return str(soup)

    def to_md(self, html_content, type_process="simple"):
        if type_process == "simple":
            return self.html2text.handle(html_content)
        elif type_process == "just_text":
            self.html2text.ignore_links = True
            res = self.html2text.handle(html_content)
            self.html2text.ignore_links = False
            return res
        return self.html2text.handle(html_content)

    def _process_head(self, html_head):
        content = BeautifulSoup(html_head, "html.parser")
        page_meta = {
            "title": content.title,
        }
        return page_meta

    def _process_body(self, html_body, page_url, split=True):
        main_content, navigation_content = self._split_html_content(html_body)
        page_meta = self._get_html_content_meta(main_content)
        main_md_content = self.to_md(str(main_content))
        if split:
            docs = self.splitter.create_documents([main_md_content], [{"source": page_url}])
            return docs, page_meta, str(navigation_content)

        return [main_md_content], page_meta, str(navigation_content)

    def _get_html_content_meta(self, html_soup):
        mark_tags = [
            "b",
            "strong",
            "i",
            "em",
            "mark",
            "small",
            "del",
            "ins",
            "sub",
            "sup",
        ]

        results = {}
        for tag in mark_tags:
            for soup_tag in html_soup.find_all(tag):
                if tag in results:
                    results[tag].append(self.to_md(str(soup_tag), type_process="just_text"))
                else:
                    results[tag] = [self.to_md(str(soup_tag), type_process="just_text")]

        page_meta = {"marked_page_tags_or_keywords": results}

        return page_meta

    def _split_html_content(self, html):
        soup = BeautifulSoup(html, "html.parser")

        main_content = BeautifulSoup('<div id="main_content"></div>', "html.parser")
        navigation_content = BeautifulSoup(
            '<div id="navigation_content"></div>', "html.parser"
        )

        main_content_div = main_content.div
        navigation_content_div = navigation_content.div

        def is_navigation_element(tag):
            navigation_classes = ["menu", "navbar", "navigation", "sidebar", "nav"]
            navigation_tags = ["nav", "header", "footer"]

            if tag.name in navigation_tags:
                return True
            if "class" in tag.attrs:
                if any(
                    nav_class in tag.get("class", [])
                    for nav_class in navigation_classes
                ):
                    return True
            return False

        def process_element(element, parent):
            # Iterate over a copy of the children to avoid modifying the list while iterating
            for child in element.contents[:]:
                if isinstance(child, Comment):
                    continue  # Skip comments
                if isinstance(child, str):
                    continue  # Skip text nodes
                if is_navigation_element(child):
                    navigation_content_div.append(child.extract())
                else:
                    # Recursively process non-navigation elements
                    process_element(child, child)

        # Start processing the body of the HTML document
        body = soup.body
        if body:
            process_element(body, main_content_div)
            main_content_div.append(body)

        return main_content, navigation_content

    def _sort_documents_by_tag_id(self, initial_order, docs_to_sort):
        def sort_key(doc):
            tag_id = doc.metadata["tag_id"]
            return initial_order.get(tag_id, float("inf"))

        sorted_docs = sorted(docs_to_sort, key=sort_key)
        return sorted_docs

    def process_page(self, html_content, page_url, split_to_chunks=True):
        content = BeautifulSoup(html_content, "html.parser")
        self.body = content.find("body")

        head = content.find("head")

        page_meta = self._process_head(str(head))
        page_meta["url"] = page_url
        page_meta["language"] = content.html["lang"]

        html_content_added_ids = self.assign_ids(str(self.body))
        self.body = html_content_added_ids

        documents, body_page_meta, navigation_content = self._process_body(
            html_content_added_ids, page_url, split=split_to_chunks
        )
        page_meta.update(body_page_meta)
        return documents, page_meta

    def process_relevant_documents(self, relevant_documents):
        results = []
        body_soup = BeautifulSoup(self.body, "html.parser")

        # Recovery documents order by html page
        ids_to_sort = {tag.get("id"): i for i, tag in enumerate(body_soup.findAll())}
        relevant_documents = self._sort_documents_by_tag_id(
            ids_to_sort, relevant_documents
        )

        return relevant_documents

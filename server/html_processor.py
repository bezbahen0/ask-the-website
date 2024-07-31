import html2text
from langchain_core.documents import Document
from bs4 import BeautifulSoup, NavigableString, Tag


class HTMLProcessor:
    def __init__(self, min_chunk_size=20, max_dom_depth=12, unicode=False):
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_images = True
        self.min_chunk_size = min_chunk_size
        self.max_dom_depth = max_dom_depth
        self.unicode = unicode
        # self.html2text.wrap_links = True
        # self.html2text.wrap_lists = True
        # self.html2text.inline_links = False
        # self.html2text.ignore_links = True

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
            "page_language": content.find("head").get("lang"),
        }
        return page_meta

    def _get_limited_depth_tag(self, tag, max_depth, current_depth=0):
        if isinstance(tag, NavigableString):
            return tag

        new_tag = Tag(name=tag.name, attrs=tag.attrs)

        if current_depth >= max_depth:
            # At max depth, only keep direct text content
            for child in tag.children:
                if isinstance(child, NavigableString):
                    new_tag.append(child)
            return new_tag

        for child in tag.children:
            new_child = self._get_limited_depth_tag(child, max_depth, current_depth + 1)
            new_tag.append(new_child)

        return new_tag

    def _process_body(self, html_body, page_url):
        content = BeautifulSoup(html_body, "html.parser")

        docs = []
        for tag in self.split_by_tags(content):
            tag_content_without_children = self._get_limited_depth_tag(
                tag, max_depth=self.max_dom_depth
            )
            text_from_tag = self.to_md(str(tag_content_without_children))
            if not self.unicode:
                text_from_tag = text_from_tag.encode("ascii", errors="ignore").decode()
            if self.min_chunk_size > len(text_from_tag):
                continue

            if text_from_tag and text_from_tag != "\n\n":

                document = Document(
                    page_content=text_from_tag.strip(),
                    metadata={
                        "source": page_url,
                        "tag_id": tag.get("id"),
                        "tag": tag.name,
                    },
                )
                docs.append(document)

        return docs

    def split_by_tags(self, html_soup):
        results = []
        for tag in html_soup.find_all(True):
            if tag.find(text=True, recursive=False):
                yield tag

    def _sort_documents_by_tag_id(self, initial_order, docs_to_sort):

        # Define a custom key function for sorting
        def sort_key(doc):
            tag_id = doc.metadata["tag_id"]
            # Return the position of the tag_id in the initial list, or a large number if not found
            return initial_order.get(tag_id, float("inf"))

        # Sort the documents using the custom key function
        sorted_docs = sorted(docs_to_sort, key=sort_key)

        return sorted_docs

    def process_page(self, html_content, page_url):
        content = BeautifulSoup(html_content, "html.parser")
        self.body = content.find("body")

        head = content.find("head")

        page_meta = self._process_head(str(head))
        page_meta["url"] = page_url

        html_content_added_ids = self.assign_ids(str(self.body))
        self.body = html_content_added_ids

        documents = self._process_body(html_content_added_ids, page_url)
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

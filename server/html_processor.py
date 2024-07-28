import html2text
from langchain_core.documents import Document
from bs4 import BeautifulSoup


class HTMLProcessor:
    def __init__(self, min_chunk_size=20, chunk_overlap=30, unicode=False):
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_images = True
        self.min_chunk_size = min_chunk_size
        self.chunk_overlap = chunk_overlap
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
        page_meta = {"title": content.title, "page_language": content.find("head").get("lang")}
        return page_meta

    def _get_tag_without_childrens(self, soup_tag):

        # copy tag
        tag = next(iter(BeautifulSoup(str(soup_tag), "html.parser")))

        for child in tag.findChildren():
            if child.name:
                child.replace_with("")

        return tag

    def _process_body(self, html_body, page_url):
        content = BeautifulSoup(html_body, "html.parser")

        docs = []
        for tag in self.split_by_tags(content):
            tag_content_without_children = self._get_tag_without_childrens(tag)
            text_from_tag = self.to_md(
                str(tag_content_without_children), type_process="just_text"
            )
            if not self.unicode:
                text_from_tag = text_from_tag.encode("ascii", errors="ignore").decode()
            if self.min_chunk_size > len(text_from_tag):
                text_from_tag = self._prepare_small_tag(tag, text_from_tag)

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
        
        sorted_docs = self._remove_subset_documents(docs)
        return sorted_docs

    def split_by_tags(self, html_soup):
        results = []
        for tag in html_soup.find_all(True):
            if tag.find(text=True, recursive=False):
                yield tag

    def _get_parent_text(self, tag):
        current = tag
        while current.parent:
            current = current.parent
            parent_text = self.to_md(str(current.parent), type_process="just_text")
            if parent_text:
                #print(parent_text)
                return parent_text
        return ""

    def _prepare_small_tag(self, tag, text):
        if text == "\n\n":
            return text

        # If tag is too small but has children with text, concatenate text with children's text
        if len(text) < self.min_chunk_size:
            children_text = self.to_md(str(tag), type_process="just_text").strip()
            if children_text:
                text = f"{text} {children_text[: self.chunk_overlap]}".strip()

        # If tag is still too small, doesn't have children with text, but has a parent with text,
        # concatenate parent's text with the current text
        if len(text) < self.min_chunk_size:
            parent_text = self._get_parent_text(tag)
            if parent_text and parent_text != text:
                parent_text = parent_text[-self.chunk_overlap:]
                

        if len(text) >= self.min_chunk_size:
            # If we've added text, make sure to include the original text fully
            return text

        return ""


    def _remove_subset_documents(self, docs):
        # Сначала сортируем документы по длине содержания (от самого длинного к самому короткому)
        sorted_docs = sorted(docs, key=lambda x: len(x.page_content), reverse=True)

        documents_to_keep = []

        for i, doc in enumerate(sorted_docs):
            is_subset = False
            for longer_doc in sorted_docs[:i]:  # Проверяем только более длинные документы
                if doc.page_content in longer_doc.page_content:
                    is_subset = True
                    break
            if not is_subset:
                documents_to_keep.append(doc)

        return documents_to_keep

    def _sort_documents_by_tag_id(self, initial_order, docs_to_sort):

        # Define a custom key function for sorting
        def sort_key(doc):
            tag_id = doc.metadata['tag_id']
            # Return the position of the tag_id in the initial list, or a large number if not found
            return initial_order.get(tag_id, float('inf'))

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
        relevant_documents = self._sort_documents_by_tag_id(ids_to_sort, relevant_documents)

        for docs in relevant_documents:
            completed_docs = self.to_md(
                str(
                    body_soup.find(
                        docs.metadata["tag"], attrs={"id": docs.metadata["tag_id"]}
                    )
                ),
                type_process="simple",
            )
            results.append(completed_docs)
        return results

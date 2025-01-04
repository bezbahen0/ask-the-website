import re
import html2text
from bs4 import BeautifulSoup, NavigableString, Tag, Comment
from pydantic import BaseModel
import pprint


class HTMLProcessingSettings(BaseModel):
    use_only_text: bool
    use_tag_attributes: bool
    concatenate_small_chunks: bool
    body: bool
    head: bool
    script: bool


class HTMLProcessor:
    def __init__(self):
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_images = True

    def to_md(self, html_content):
        return self.html2text.handle(html_content)

    def is_full_page(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.find("html") != None

    def _prepare_html_tag(self, html_tag, only_visual_tags, tag_attributes):
        html_tag = BeautifulSoup(html_tag, "html.parser")
        for tag in html_tag.find_all(True):
            if only_visual_tags:
                if tag.name in ["style", "script", "svg"]:
                    tag.decompose()
                    continue

            if not tag_attributes:
                if tag.attrs:
                    attrs_to_keep = ["href"]
                    tag.attrs = {
                        attr: value
                        for attr, value in tag.attrs.items()
                        if attr in attrs_to_keep
                    }
        return html_tag.prettify()

    def _find_parent_path(self, tag):
        tree = []
        tag = tag.find_parent()
        while tag.name != "html":
            path_name = tag.name + " > "
            tree.append(path_name)
            tag = tag.find_parent()
        tree.reverse()
        return "".join(tree)

    def _split_tags_tree(self, tag, context_len_checker=None):
        if context_len_checker is None:
            return [str(tag)]

        tag_str = str(tag)
        if context_len_checker(tag_str):
            return [tag_str]

        if isinstance(tag, NavigableString) or isinstance(tag, Comment):
            return [str(tag)]

        result = []
        for child in tag.children:
            child_chunks = self._split_tags_tree(child, context_len_checker)
            result.extend(child_chunks)

        if not result:
            return [tag_str]

        return result

    def _process_head(self, html_head):
        content = BeautifulSoup(html_head, "html.parser")
        page_meta = {
            "title": content.title,
        }
        return page_meta

    def _process_body(
        self,
        html_body,
        page_url,
        split,
        only_visual_tags,
        tag_attributes,
        concatenate_small_chunks,
        context_len_checker=None,
    ):
        html_content = self._prepare_html_tag(
            str(html_body), only_visual_tags, tag_attributes
        )
        page_meta = None

        if split:
            html_body = BeautifulSoup(
                str(html_content).replace("\\n", ""), "html.parser"
            )

            docs = self._split_tags_tree(
                html_body, context_len_checker=context_len_checker
            )
            if concatenate_small_chunks:
                docs = self._concatenate_small_docs(
                    docs, context_len_checker=context_len_checker
                )
            docs = [d.strip() for d in docs if d.strip()]
            return docs, page_meta

        return html_content, page_meta

    def _concatenate_small_docs(self, docs, context_len_checker):
        if not docs:
            return []

        concatenated_docs = []
        current_doc = ""

        for doc in docs:
            if not doc:
                continue

            if current_doc:
                combined_doc = f"{current_doc}\n\n{doc}"
            else:
                combined_doc = doc

            if context_len_checker(combined_doc):
                current_doc = combined_doc
            else:
                if current_doc:
                    concatenated_docs.append(current_doc)
                if context_len_checker(doc):
                    current_doc = doc
                else:
                    continue

        if current_doc:
            concatenated_docs.append(current_doc)

        return concatenated_docs

    def make_page(self, html_tags_list, old_responses_list, processing_settings):

        if not processing_settings.use_only_text:
            root_tag = BeautifulSoup("<body></body>", "html.parser")
            body = root_tag.body

            for i, tag_string in enumerate(html_tags_list):
                tag = BeautifulSoup(tag_string, "html.parser").contents[0]

                if not isinstance(tag, NavigableString):
                    tag.clear()
                tag.string = f"{old_responses_list[i]}"

                body.append(tag)
                body.append("\n\n")

            return root_tag.prettify()

        return "\n\n".join(html_tags_list)

    def process_page(
        self,
        html_content,
        page_url,
        processing_settings,
        split=False,
        context_len_checker=None,
    ):

        content = BeautifulSoup(html_content, "html.parser")

        if processing_settings.use_only_text:
            if not split:
                return self.to_md(html_content)

            documents, body_page_meta = self._process_body(
                content,
                page_url,
                split=split,
                tag_attributes=True,
                only_visual_tags=True,
                concatenate_small_chunks=processing_settings.concatenate_small_chunks,
                context_len_checker=context_len_checker,
            )

            documents = [
                self.to_md(doc).strip() for doc in documents if self.to_md(doc).strip()
            ]
            pprint.pp(documents)
            return documents

        if processing_settings.head:
            head = content.find("head")

            if head:
                page_meta = self._process_head(str(head))
                page_meta["url"] = page_url
                if "lang" in content.html:
                    page_meta["language"] = content.html["lang"]
            else:
                page_meta = {}

        if processing_settings.body:
            body = content.find("body")
            if not body:
                body = content

            documents, body_page_meta = self._process_body(
                body,
                page_url,
                split=split,
                tag_attributes=processing_settings.use_tag_attributes,
                only_visual_tags=not processing_settings.script,
                concatenate_small_chunks=processing_settings.concatenate_small_chunks,
                context_len_checker=context_len_checker,
            )
            return documents

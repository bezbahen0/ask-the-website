import re
import html2text
from langchain_core.documents import Document
from bs4 import BeautifulSoup, NavigableString, Tag, Comment

from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)

import pprint


class HTMLProcessor:
    def __init__(self, min_chunk_len=128, chunk_overlap=40, unicode=False):
        self.min_chunk_len = min_chunk_len

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
            if self.html2text.ignore_links:
                res = self.html2text.handle(html_content)
            else:
                self.html2text.ignore_links = True
                res = self.html2text.handle(html_content)
                self.html2text.ignore_links = False
            return res
        return self.html2text.handle(html_content)

    def _prepare_html_tag(self, html_tag, only_visual_tags, tag_attributes):
        html_tag = BeautifulSoup(html_tag, "html.parser")
        for tag in html_tag.find_all(True):
            if only_visual_tags:
                if tag.name in ["style", "script", "svg"]:
                    tag.decompose()
                    continue
            else:
                if tag.name not in ["style", "script", "svg"]:
                    tag.decompose()
                    continue

            if not tag_attributes:
                tag.attrs = {}
        return str(html_tag)

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

            docs = self._split_tags_tree(html_body, context_len_checker)
            docs = [d.strip() for d in docs if d.strip()]
            return docs, page_meta

        return [html_content], page_meta

    def make_page(self, html_tags_list, current_iter, old_responses_list):
        root_tag = BeautifulSoup("<body></body>", "html.parser")
        body = root_tag.body

        for i, tag_string in enumerate(html_tags_list):
            tag = BeautifulSoup(tag_string, "html.parser").contents[0]

            if i > current_iter:
                tag.clear()
                tag.string = "MASKED: Will be shown later"
            elif i < current_iter:
                tag.clear()
                tag.string = f"This part of the html has already been viewed, here is the answer for it: \n{old_responses_list[i]}"

            body.append(tag)
            body.append("\n\n")

        return root_tag.prettify()

    def process_page(
        self,
        html_content,
        page_url,
        split=False,
        only_visual_tags=True,
        tag_attributes=True,
        context_len_checker=None,
    ):
        content = BeautifulSoup(html_content, "html.parser")

        self.body = content.find("body")
        if not self.body:
            self.body = content

        head = content.find("head")

        if head:
            page_meta = self._process_head(str(head))
            page_meta["url"] = page_url
            if "lang" in content.html:
                page_meta["language"] = content.html["lang"]
        else:
            page_meta = {}

        documents, body_page_meta = self._process_body(
            self.body,
            page_url,
            split=split,
            only_visual_tags=only_visual_tags,
            tag_attributes=tag_attributes,
            context_len_checker=context_len_checker,
        )
        # page_meta.update(body_page_meta)
        return documents, body_page_meta

from typing import List, Optional
from dataclasses import dataclass, field


newline = "\n"
newline_l = len(newline)


@dataclass(frozen=True, slots=True)
class Header:
    level: int
    text: str
    line_number: int
    start_at: int  # start from 0
    page_number: int  # start from 1
    children: List["Header"] = field(default_factory=list)

    @property
    def header_length(self) -> int:
        return len(self.text)


@dataclass(frozen=True, slots=True)
class Chunk:
    pages: List[int]
    text: str
    length: int


class MarkdownParser:
    """
    Parser class to extract headers (H1, H2, H3) from markdown text.
    Preserves the order of headers and ignores headers smaller than H4.
    """

    def __init__(self):
        self.headers: List[Header] = []
        self.all_text: str = ""
        self.all_line_number: int = 0
        self.all_text_length: int = 0
        self.total_pages: int = 0
        self._header_stack: List[Header] = []

    def reset(self) -> None:
        """
        Clear all parsed headers, resetting the parser to its initial state.
        """
        self.headers.clear()
        # delete all the text
        self.all_text = ""
        self.all_line_number = 0
        self.all_text_length = 0
        self.total_pages = 0
        self._header_stack: List[Header] = []

    def add(self, markdown_text: str) -> None:
        """
        Add markdown text and extract headers.
        """
        if not markdown_text:
            return []

        # Add to all markdown text
        self.all_text += markdown_text + newline
        self.total_pages += 1

        # Parse the headers
        for line in markdown_text.split(newline):
            self.all_line_number += 1
            self.all_text_length += len(line) + newline_l
            self._parse_line(line)

    def trim_before_markdown_begin(self, text: str) -> str:
        """
        Trim everything before the first `#` appears.
        """
        first_hash_index = text.find("#")
        if first_hash_index == -1:
            return ""
        return text[first_hash_index:]

    def _parse_line(self, line: str) -> Optional[Header]:
        """
        Parse a single line to check if it's a header and build hierarchy.
        """
        stripped = line.strip()

        # Check if line starts with # symbols
        if not stripped.startswith("#"):
            return None

        # Count consecutive # symbols at the start
        level = 0
        for char in stripped:
            if char == "#":
                level += 1
            else:
                break

        # Return None if header text is empty (after removing # symbols)
        text_after_hash = stripped[level:].strip()
        if not text_after_hash:
            return None

        # Create the header
        header = Header(
            level=level,
            text=stripped,
            start_at=self.all_text_length - len(line) - newline_l,
            line_number=self.all_line_number,
            page_number=self.total_pages,
            children=[],
        )

        # Build hierarchy using stack
        if not self._header_stack:
            # First header, add to root
            self.headers.append(header)
            self._header_stack.append(header)
        else:
            # Find the appropriate parent by traversing up the stack
            parent = None
            # Pop headers from stack until we find one with level < current level
            while self._header_stack:
                candidate = self._header_stack[-1]
                if candidate.level < level:
                    # Found suitable parent
                    parent = candidate
                    break
                # Current level is <= candidate level, pop and continue
                self._header_stack.pop()

            if parent is None:
                # No suitable parent found, add to root
                self.headers.append(header)
                self._header_stack = [header]  # Reset stack with this header
            else:
                # Add as child of parent
                # Since Header is frozen, we need to work with mutable children list
                # The children list itself is mutable even if Header is frozen
                parent.children.append(header)
                self._header_stack.append(header)

        return header

    def get_headers(self) -> List[Header]:
        """
        Get the list of parsed headers.
        """
        return self.headers.copy()

    def outline(self, max_level: int = 3, max_length: int = 50) -> str:
        """
        Return all headers as a concatenated string, with each header separated by a newline.
        """
        if not self.headers:
            return ""

        # Helper function to recursively collect headers
        def collect_headers(header: Header) -> List[str]:
            """Recursively collect header lines including children."""
            result = []

            # Process current header if it meets max_level criteria
            if header.level <= max_level:
                # Text already includes # symbols, use it as-is
                header_line = header.text

                # Truncate if max_length is specified and header exceeds it
                if max_length is not None and header.header_length > max_length:
                    # Account for the "..." suffix
                    truncate_at = max_length - 3
                    if (
                        truncate_at < header.level + 1
                    ):  # Ensure we keep at least the # symbols
                        truncate_at = header.level + 1
                    header_line = header_line[:truncate_at] + "..."

                result.append(header_line)

            # Recursively process children
            for child in header.children:
                result.extend(collect_headers(child))

            return result

        # Collect all headers recursively
        filtered_headers = []
        for header in self.headers:
            filtered_headers.extend(collect_headers(header))

        return newline.join(filtered_headers)

    def short_outline(self, max_length: int = 5000) -> str:
        """
        Create a short outline by packing headers
        """
        if not self.headers:
            return ""

        # Helper function to get the deepest child of a header
        def get_deepest_child(header: Header) -> Header:
            """Recursively find the deepest child of a header."""
            if not header.children:
                return header
            return get_deepest_child(header.children[-1])

        # Helper function to flatten all headers with metadata
        def flatten_headers(
            headers_list: List[Header],
            top_level_index: int,
            global_index: int = 0,
            depth: int = 0,
        ) -> tuple:
            """
            Flatten headers with their metadata: (header, top_level_index, global_index, depth)
            Returns tuple of (result_list, next_global_index)
            """
            result = []
            current_global_index = global_index
            for idx, header in enumerate(headers_list):
                result.append((header, top_level_index, current_global_index, depth))
                current_global_index += 1
                # Recursively add children
                if header.children:
                    child_results, current_global_index = flatten_headers(
                        header.children,
                        top_level_index,
                        current_global_index,
                        depth + 1,
                    )
                    result.extend(child_results)
            return result, current_global_index

        # Get all headers flattened with top-level index tracking
        all_headers_flat = []
        global_idx = 0
        for top_idx, top_header in enumerate(self.headers):
            header_list, global_idx = flatten_headers(
                [top_header], top_idx, global_idx, 0
            )
            all_headers_flat.extend(header_list)

        if not all_headers_flat:
            return ""

        # Rule 1: First header must be included
        first_header = all_headers_flat[0][0]
        first_line = first_header.text
        first_length = first_header.header_length + newline_l

        # Rule 2: Last title (deepest child of last header) must be included
        last_top_header = self.headers[-1]
        last_deepest_header = get_deepest_child(last_top_header)
        last_line = last_deepest_header.text
        last_length = last_deepest_header.header_length + newline_l

        # Calculate available length
        available_length = max_length - first_length
        if last_deepest_header != first_header:
            available_length -= last_length

        # If we don't have enough space even for first and last, return minimal outline
        if available_length < 0:
            result_lines = [first_line]
            if last_deepest_header != first_header:
                result_lines.append("...")
                result_lines.append(last_line)
            return newline.join(result_lines)

        # Rule 3, 4, 5: Pack remaining headers by priority
        # Priority order:
        # 1. Higher level (H1 > H2 > H3) = higher priority (lower level number = higher priority)
        # 2. Higher top-level index = higher priority
        # 3. Parent before children (lower depth = higher priority)

        # Create list of headers to prioritize (exclude first and last)
        headers_to_pack = []
        for header, top_idx, global_idx, depth in all_headers_flat:
            if header == first_header or header == last_deepest_header:
                continue
            headers_to_pack.append((header, top_idx, global_idx, depth))

        # Sort by priority:
        # 1. Level (ascending: H1=1, H2=2, H3=3, so lower number = higher priority)
        # 2. Top-level index (descending: higher index = higher priority)
        # 3. Depth (ascending: parent before children)
        headers_to_pack.sort(key=lambda x: (x[0].level, -x[1], x[3]))

        # Pack headers in priority order
        packed_headers = []
        for header, top_idx, global_idx, depth in headers_to_pack:
            header_length = header.header_length + newline_l
            if available_length >= header_length:
                packed_headers.append((header, global_idx))
                available_length -= header_length
            else:
                break

        # Sort packed headers by their original global index to maintain order
        packed_headers.sort(key=lambda x: x[1])
        packed_header_objects = [h[0] for h in packed_headers]

        # Build result lines maintaining order
        result_lines = [first_line]

        # Add packed headers in their original order
        for header, top_idx, global_idx, depth in all_headers_flat:
            if header in packed_header_objects:
                result_lines.append(header.text)

        # Add "..." if we couldn't pack all headers
        if len(packed_headers) < len(headers_to_pack):
            result_lines.append("...")

        # Add last header at the end
        if last_deepest_header != first_header:
            result_lines.append(last_line)

        return newline.join(result_lines)

    def chunk(self, size: int) -> List[Chunk]:
        """
        Chunk the markdown text into chunks of size.
        Chunks are created at header boundaries, ensuring each chunk doesn't exceed the size limit.
        """
        if self.total_pages == 0:
            return []

        if self.all_text_length <= size:
            return [
                Chunk(
                    pages=list(range(1, self.total_pages + 1)),
                    text=self.all_text,
                    length=self.all_text_length,
                )
            ]

        result = []

        def collect_pages(header: Header) -> List[int]:
            """Collect all page numbers from header and its children."""
            pages = [header.page_number]
            for child in header.children:
                pages.extend(collect_pages(child))
            # Remove duplicates while preserving order
            seen = set()
            unique_pages = []
            for page in pages:
                if page not in seen:
                    seen.add(page)
                    unique_pages.append(page)
            return unique_pages

        def get_all_headers_flat(header: Header) -> List[Header]:
            """Flatten header and all its children in order."""
            headers = [header]
            for child in header.children:
                headers.extend(get_all_headers_flat(child))
            return headers

        # If no headers, chunk by size without header boundaries
        if not self.headers:
            chunks = []
            start = 0
            while start < self.all_text_length:
                end = min(start + size, self.all_text_length)
                chunk_text = self.all_text[start:end]
                # Determine which pages this chunk spans
                # This is approximate - we'd need to track page boundaries for accuracy
                pages = list(range(1, self.total_pages + 1))
                chunks.append(
                    Chunk(pages=pages, text=chunk_text, length=len(chunk_text))
                )
                start = end
            return chunks

        # Collect all headers in order (flattening the hierarchy)
        all_headers = []
        for header in self.headers:
            all_headers.extend(get_all_headers_flat(header))

        if not all_headers:
            return result

        # Process headers to create chunks
        chunk_start = all_headers[0].start_at
        chunk_headers = [all_headers[0]]

        for i, header in enumerate(all_headers[1:], 1):
            # Calculate chunk size if we include this header
            chunk_end = header.start_at
            chunk_length = chunk_end - chunk_start

            # If adding this header would exceed size, finalize current chunk
            if chunk_length > size:
                # Create chunk ending at the last successfully added header
                # Find where the last header in chunk_headers ends
                last_header_idx = all_headers.index(chunk_headers[-1])
                if last_header_idx + 1 < len(all_headers):
                    actual_chunk_end = all_headers[last_header_idx + 1].start_at
                else:
                    actual_chunk_end = self.all_text_length

                chunk_text = self.all_text[chunk_start:actual_chunk_end]

                # Collect pages from headers in this chunk
                pages = []
                for h in chunk_headers:
                    pages.extend(collect_pages(h))
                # Remove duplicates while preserving order
                seen = set()
                unique_pages = []
                for page in pages:
                    if page not in seen:
                        seen.add(page)
                        unique_pages.append(page)

                result.append(
                    Chunk(pages=unique_pages, text=chunk_text, length=len(chunk_text))
                )

                # Start new chunk from current header
                chunk_start = header.start_at
                chunk_headers = [header]
            else:
                # Add header to current chunk
                chunk_headers.append(header)

        # Handle the last chunk (from last chunk_start to end of text)
        if chunk_start < self.all_text_length:
            last_chunk_text = self.all_text[chunk_start:]

            # Collect pages from remaining headers
            pages = []
            for h in chunk_headers:
                pages.extend(collect_pages(h))
            # Remove duplicates while preserving order
            seen = set()
            unique_pages = []
            for page in pages:
                if page not in seen:
                    seen.add(page)
                    unique_pages.append(page)

            result.append(
                Chunk(
                    pages=unique_pages,
                    text=last_chunk_text,
                    length=len(last_chunk_text),
                )
            )

        return result


if __name__ == "__main__":
    markdown_text = "markdown\n# 買取契約基本契約書\n\n## 株式会社GROWTH（以下「売主」という。）と株式会社STANDAGE（以下「買主」という。）は、売主と買主との間における第1条に定める本件商品の売買について、以下のとおり取引基本契約（以下「本契約」という。）を締結する。\n\n---\n\n### 第1条（目的となる商品）\n本契約の目的となる商品（以下「本件商品」という。）は、売主が取り扱うすべての商品とする。ただし、売主は、買主と協議の上、本件商品の内容を変更することができる。\n\n---\n\n### 第2条（基本契約）\n1. 本契約は、売主が買主に対して本件商品を売り渡す売買契約（以下「個別契約」という。）の全部に適用される。\n2. 個別契約と異なる内容を定めた場合は、個別契約が本契約に優先する。\n\n---\n\n### 第3条（個別契約）\n1. 個別契約は、買主が売主に対し、本件商品の名称、数量、単価、引渡日及び引渡場所その他必要な事項として売主が定める事項を記載した書面を送付する方法により申し込み、これに対し、売主が承諾する旨の通知を発したときに成立する。\n2. 買主が売主に対して前項の書面を送付した日から10営業日以内に、売主から買主に対する承諾の通知を発しない場合、買主による当該申し込みは効力を失う。\n3. 前2項の規定は、売主及び買主協議の上でこれに代わる方法を定めることを妨げない。\n\n---\n\n### 第4条（納入）\n売主は、買主に対し、個別契約で定めた納入日に、個別契約で定めた納入場所で、本件商品を納入する。\n\n---\n\n### 第5条（検査）\n1. 買主は、本件商品を受領後10営業日以内に、本件商品の内容を検査し、検査に合格したものを検収する。買主は、本件商品に種類、品質又は数量その他本契約の内容との不適合がある場合、売主に対して、10営業日以内にその旨を通知しなければならない。なお、本件商品の受領後10営業日以内に買主が売主への通知が無い場合は、買主により本件商品の内容が合格と判断されたものとみなす。\n2. 本件商品が前項の検査に合格する場合、買主は、売主に対し、検査合格書を交付し、当該検査の合格をもって、本件商品の検収が完了したものとする。\n\n---\n\n### 第6条（引渡し）\n売主から買主の本件商品の引渡しは、個別契約で定められた納入場所に本件商品が納入されたときに完了する。\n\n---\n\n### 第7条（所有権の移転）\n本件商品の所有権は、商品の納品時をもって、目的物の所有権が移転する。\n\n---\n\n### 第8条（危険負担）\n本件商品について生じた減失、毀損その他の危険は、引渡し前に生じたものは買主の責めに帰すべき事由がある場合は除き売主の、引渡し後に生じたものは売主の責めに帰すべき事由がある場合は除き買主の負担とする。\n\n---\n\n### 第9条（代金支払）\n買主は、毎月末日までに納入を受けた本件商品の代金を、翌月末日（金融機関が休業日の場合は前営業日）までに売主が指定する銀行口座宛に振込みする方法により支払う。ただし、振込手数料は買主の負担とする。"

    # Parse markdown and extract headers
    parser = MarkdownParser()
    parser.add(markdown_text)
    parser.add(markdown_text)
    # for index, header in enumerate(parser.headers):
    #     print(index, header.level, header.text)
    #     for index, child in enumerate(header.children):
    #         print("  ", index, child.level, child.text)
    #         for index, grandchild in enumerate(child.children):
    #             print("    ", index, grandchild.level, grandchild.text)
    # print(parser.outline(3))
    # print("-" * 50)
    # print(parser.short_outline(300))
    # print(parser.all_text_length)
    # print(parser.all_line_number)
    # print(parser.all_text)

    chunks = parser.chunk(1000)
    for chunk in chunks:
        print("pages:", chunk.pages)
        print("text:", chunk.text)
        print("length:", chunk.length)
        print("***" * 50)

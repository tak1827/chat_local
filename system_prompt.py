from typing import List
from chunks_table import ChunkTable

SYSTEM_PROMPT_MARKDOWN = """
Convert to markdown format without any other text. For images of the page, you should describe the image in detail.
"""


def get_markdown_prompt(outline: str) -> str:
    if not outline:
        return SYSTEM_PROMPT_MARKDOWN
    else:
        return f"""
{SYSTEM_PROMPT_MARKDOWN}

The page is not the first page, and the outline of previous pages is provided. Please continue the markdown from the outline.
Outline:
{outline}

Start the markdown. No outline should be included in the markdown.
"""


def get_rewrite_question_prompt(question: str) -> str:
    return f"""
Rewrite the following question into a factual statement
that would appear in documentation.

Question:
"{question}"
"""


def get_answer_prompt(question: str, chunks: List[ChunkTable]) -> str:
    concated_chunks = "\n".join([f"{chunk.content}\n\n" for chunk in chunks])
    return f"""
Answer the following question based on the provided chunks.

Question:
"{question}"

Chunks:
{concated_chunks}
"""

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

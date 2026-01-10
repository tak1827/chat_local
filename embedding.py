import base64
from io import BytesIO
from pathlib import Path
from pypdf import PdfReader
from pdf2image import convert_from_path
from llm_client import LLMClient
from db_client import DatabaseClient
from markdown_parser import MarkdownParser
from system_prompt import get_markdown_prompt

# Supported file types
SUPPORTED_FILE_TYPES = [".pdf"]

# DPI mapping
DPI_MAP = {
    "low": 50,
    "middle": 100,
    "high": 200,
}


def embed_file(
    client: LLMClient,
    db_client: DatabaseClient,
    parser: MarkdownParser,
    file_path: Path,
    dpi: int = DPI_MAP["middle"],
) -> None:
    """Embed a file into the database."""
    # Sanity checks the path to be a file
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    # if file is pdf
    if file_path.suffix.lower() == ".pdf":
        return embed_pdf(client, db_client, parser, file_path, dpi=dpi)

    # TODO: support other file types

    # Throw an error for unsupported file types
    raise ValueError(f"Unsupported file type: {file_path.suffix.lower()}")


def embed_pdf(
    client: LLMClient,
    db_client: DatabaseClient,
    parser: MarkdownParser,
    file_path: Path,
    dpi: int = DPI_MAP["middle"],
) -> None:
    """Embed a PDF file"""
    # load each pages of the PDF file
    reader = PdfReader(str(file_path))

    # reset the parser before parsing
    parser.reset()

    for page_num in range(len(reader.pages)):
        # convert the page to image
        images = convert_from_path(
            str(file_path),
            first_page=page_num + 1,
            last_page=page_num + 1,
            dpi=dpi,
        )

        # exactly one image
        image = images[0]
        # image.save(f"page_{page_num + 1}.png", "PNG")

        # convert to base64
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # convert the image to markdown
        short_outline = parser.short_outline(200)
        system_prompt = get_markdown_prompt(short_outline)
        raw_output = client.chat_completion_with_image(system_prompt, base64_image)
        markdown_text = parser.trim_before_markdown_begin(raw_output)

        # print the response
        print("outline:")
        print(short_outline)
        print("-" * 50)
        print("response:")
        print(markdown_text)
        print("-" * 50)

        # Add to parse the markdown
        parser.add(markdown_text)

    # print the outline
    print("all outlines:")
    print(parser.outline())

    # chunk the markdown text
    chunks = parser.chunk(1024)
    for chunk in chunks:
        print("pages:", chunk.pages)
        print("length:", chunk.length)
        print("text:", chunk.text)
        # embed the chunk into the database
        embedding = client.get_embedding(chunk.text)
        print("embedding:", len(embedding))
        print("***" * 50)

        # Extract title from file path
        title = file_path.stem[:50].strip()

        # Save chunk using database client
        chunk_id = db_client.save_chunk(
            title=title,
            content=chunk.text,
            embedding=embedding,
            meta={
                "pages": chunk.pages,
                "length": chunk.length,
                "file_path": str(file_path),
            },
        )
        print(f"Saved chunk to database with ID: {chunk_id}")

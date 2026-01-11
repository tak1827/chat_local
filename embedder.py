import base64
from typing import Iterator
from io import BytesIO
from pathlib import Path
from pypdf import PdfReader
from pdf2image import convert_from_path
from llm_client import LLMClient
from markdown_parser import MarkdownParser
from system_prompt import get_markdown_prompt
from chunks_table import ChunkTable

# Supported file types
SUPPORTED_FILE_TYPES = [".pdf"]

# DPI mapping
DPI_MAP = {
    "low": 50,
    "middle": 100,
    "high": 200,
}


class Embedder:
    """Class for embedding files into the database."""

    def __init__(self, client: LLMClient):
        """
        Initialize the Embedder.
        """
        self.client = client
        self.parser = MarkdownParser()

    def embed_file(
        self,
        file_path: Path,
        dpi: int = DPI_MAP["middle"],
    ) -> Iterator[ChunkTable]:
        """Embed a file into the database."""
        # Sanity checks the path to be a file
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # if file is pdf
        if file_path.suffix.lower() == ".pdf":
            return self.embed_pdf(file_path, dpi=dpi)

        # TODO: support other file types

        # Throw an error for unsupported file types
        raise ValueError(f"Unsupported file type: {file_path.suffix.lower()}")

    def embed_pdf(
        self,
        file_path: Path,
        dpi: int = DPI_MAP["middle"],
    ) -> Iterator[ChunkTable]:
        """Embed a PDF file"""
        # load each pages of the PDF file
        reader = PdfReader(str(file_path))

        # reset the parser before parsing
        self.parser.reset()

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
            short_outline = self.parser.short_outline(200)
            system_prompt = get_markdown_prompt(short_outline)
            raw_output = self.client.chat_completion_with_image(
                system_prompt, base64_image
            )
            markdown_text = self.parser.trim_before_markdown_begin(raw_output)

            # print the response
            print("outline:")
            print(short_outline)
            print("-" * 50)
            print("response:")
            print(markdown_text)
            print("-" * 50)

            # Add to parse the markdown
            self.parser.add(markdown_text)

        # print the outline
        print("all outlines:")
        print(self.parser.outline())

        # chunk the markdown text
        chunks = self.parser.chunk(1024)
        for chunk in chunks:
            print("pages:", chunk.pages)
            print("length:", chunk.length)
            print("text:", chunk.text)
            # embed the chunk into the database
            embedding = self.client.get_embedding(chunk.text)
            print("embedding:", len(embedding))
            print("***" * 50)

            # Extract title from file path
            title = file_path.stem[:50].strip()
            chunk_table = ChunkTable(
                title=title,
                content=chunk.text,
                embedding=embedding,
                meta={
                    "pages": chunk.pages,
                    "length": chunk.length,
                    "file_path": str(file_path),
                },
            )
            yield chunk_table

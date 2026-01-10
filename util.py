from pathlib import Path
from pypdf import PdfReader
from typing import Callable
import base64
import typer


def parse_pdf(path_obj: Path) -> str:
    """
    Parse a PDF file and return the extracted text.

    Args:
        path: Path to the PDF file

    Returns:
        Extracted text from the PDF
    """
    # Validate file exists
    if not path_obj.exists():
        raise FileNotFoundError(f"PDF file not found: {path_obj}")

    # Validate it's a file
    if not path_obj.is_file():
        raise ValueError(f"Path is not a file: {path_obj}")

    # Validate it's a PDF
    if path_obj.suffix.lower() != ".pdf":
        raise ValueError(f"File is not a PDF: {path_obj}")

    # Read and extract text from PDF
    reader = PdfReader(str(path_obj))
    text_parts = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
            # print the content of the page
            typer.echo(f"📄 Page {page.page_number}:")
            typer.echo("=" * 40)
            text = base64.b64encode(text.encode("utf-8")).decode("utf-8")
            typer.echo(text)
            typer.echo("=" * 40)

    return "\n".join(text_parts)


def prompt_for_path() -> str:
    typer.echo("🔍 Interactive Path Input Tool")
    typer.echo("=" * 40)
    path = input("Enter a file or directory path: ").strip()
    if not path:
        raise ValueError("Path cannot be empty. Please try again.")
    return path


def validate_path(path: str) -> Path:
    path_obj = Path(path)
    if not path_obj.exists():
        raise ValueError(f"Path does not exist: {path_obj}")
    return path_obj


def return_recursive_file_paths(
    path: Path, is_supported_file_type: Callable[[Path], bool]
) -> list[Path]:
    if path.is_file():
        if is_supported_file_type(path):
            return [path]
        else:
            return []
    # load files in the directory recursively
    file_paths = []
    for file in path.glob("**/*"):
        if file.is_file() and is_supported_file_type(file):
            file_paths.append(file)
    return file_paths

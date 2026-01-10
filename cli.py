import os
import typer
from pathlib import Path
from typing import Optional, Literal
from util import prompt_for_path, validate_path, return_recursive_file_paths
from llm_client import LLMClient
from db_client import DatabaseClient
from markdown_parser import MarkdownParser
from embedding import embed_file, DPI_MAP, SUPPORTED_FILE_TYPES

app = typer.Typer()


@app.command()
def emb(
    path: Optional[str] = typer.Argument(None, help="Path to file or directory"),
    resolution: Literal["low", "middle", "high"] = typer.Option(
        "middle",
        "--resolution",
        "-r",
        help="Image resolution: low (100dpi), middle (150dpi), high (200dpi)",
    ),
):
    """Embed a file or directory into the database."""
    try:
        if not path:
            path = prompt_for_path()

        # validate the path
        path_obj = validate_path(path)

        # return the recursive file paths
        def is_supported_file_type(path: Path) -> bool:
            return path.suffix.lower() in SUPPORTED_FILE_TYPES

        file_paths = return_recursive_file_paths(path_obj, is_supported_file_type)
        if not file_paths:
            raise ValueError("No supported files found in the directory.")

        # Get DPI from resolution setting
        dpi = DPI_MAP[resolution]
        typer.echo(f"Using resolution: {resolution} ({dpi} DPI)")

        client = LLMClient(
            os.getenv("LLM_API_BASE_URL"),
            os.getenv("INFER_MODEL"),
            os.getenv("EMBEDDING_MODEL"),
        )
        db_client = DatabaseClient()
        parser = MarkdownParser()

        # Use nested context managers for proper resource management
        with client:
            with db_client:
                for file_path in file_paths:
                    typer.echo(f"Embedding file: {file_path}")
                    embed_file(client, db_client, parser, file_path, dpi=dpi)

    except Exception as e:
        typer.echo(f"❌ Error: {e}")
        exit(1)


if __name__ == "__main__":
    app()

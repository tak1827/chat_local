import os
import base64
import typer
from pathlib import Path
from typing import Optional, Literal
from util import prompt_for_path, validate_path, return_recursive_file_paths
from llm_client import LLMClient
from db_client import DatabaseClient
from embedding import Embedder, DPI_MAP, SUPPORTED_FILE_TYPES

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

        with db_client:
            embedder = Embedder(client)
            for file_path in file_paths:
                for chunk_table in embedder.embed_file(file_path, dpi=dpi):
                    print("***" * 50)
                    chunk_id = db_client.save_chunk(chunk_table)
                    typer.echo(f"Saved chunk to database with ID: {chunk_id}")

    except Exception as e:
        typer.echo(f"❌ Error: {e}")
        exit(1)


@app.command()
def img_to_base64(
    path: Optional[str] = typer.Argument(None, help="Path to image file"),
):
    """Convert an image file to base64 format."""
    try:
        if not path:
            path = prompt_for_path()

        path_obj = Path(path)

        # Validate that the path exists and is a file
        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {path}")

        # Check if it's an image file (basic check)
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
        if path_obj.suffix.lower() not in image_extensions:
            typer.echo(
                f"⚠️  Warning: File extension '{path_obj.suffix}' may not be a standard image format",
                err=True,
            )

        # Read the image file as binary and convert to base64
        with open(path_obj, "rb") as image_file:
            image_bytes = image_file.read()
            base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # Output the base64 string
        typer.echo(base64_image)

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        exit(1)


if __name__ == "__main__":
    app()

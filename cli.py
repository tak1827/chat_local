import os
import base64
import typer
from pathlib import Path
from typing import Optional, Literal
from util import (
    prompt_for_path,
    prompt_for_text,
    validate_path,
    return_recursive_file_paths,
)
from llm_client import LLMClient
from db_client import DatabaseClient
from embedder import Embedder, DPI_MAP, SUPPORTED_FILE_TYPES
from system_prompt import get_rewrite_question_prompt, get_answer_prompt
from logger import get_logger

app = typer.Typer()
logger = get_logger(__name__)


@app.command()
def infer(
    question: str = typer.Argument(None, help="Question to infer"),
):
    try:
        if not question:
            # Obtain the question from the user interactively
            question = prompt_for_text()

        client = LLMClient(
            os.getenv("LLM_API_BASE_URL"),
            os.getenv("INFER_MODEL"),
            os.getenv("EMBEDDING_MODEL"),
        )

        # Rewrite the question expanding the context of the question to retrieve more relevant chunks
        prompt = get_rewrite_question_prompt(question)
        rewritten_question = client.chat_completion_without_image(prompt)
        embeddings = client.get_embedding(rewritten_question)

        with DatabaseClient() as db_client:
            # Retrieve the similar chunks from the database
            chunks_with_distance = db_client.similar_chunks(embeddings)
            for chunk, distance in chunks_with_distance:
                logger.debug(f"Similar chunk: {chunk.title}")
                logger.debug(f"Distance: {distance}")
                logger.debug(f"Content: {chunk.content}")
                logger.debug("-" * 50)

            # Extract just the chunks (first element of each tuple) for the prompt
            chunks_only = [chunk for chunk, distance in chunks_with_distance]
            answer_prompt = get_answer_prompt(question, chunks_only)
            response = client.chat_completion_without_image(answer_prompt)
            typer.echo("Answer:")
            typer.echo("=" * 50)
            typer.echo(response)

    except Exception as e:
        logger.error(f"Error: {e}")
        exit(1)


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

        with DatabaseClient() as db_client:
            embedder = Embedder(client)
            for file_path in file_paths:
                for chunk_table in embedder.embed_file(file_path, dpi=dpi):
                    logger.debug("***" * 50)
                    chunk_id = db_client.save_chunk(chunk_table)
                    logger.info(f"Saved chunk to database with ID: {chunk_id}")

    except Exception as e:
        logger.error(f"Error: {e}")
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
            logger.warning(
                f"File extension '{path_obj.suffix}' may not be a standard image format"
            )

        # Read the image file as binary and convert to base64
        with open(path_obj, "rb") as image_file:
            image_bytes = image_file.read()
            base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # Output the base64 string
        typer.echo(base64_image)

    except Exception as e:
        logger.error(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    app()

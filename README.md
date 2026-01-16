# Getting Started
## Prerequisites
- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- PostgreSQL 17 with pgvector extension

```sh
# Install PostgreSQL, pgvector extension and uv
brew install postgresql@17 pgvector uv
```

## Setting Up the Database
```sh
# Start PostgreSQL service
brew services start postgresql@17

# Show status
brew services info postgresql@17

# Create a PostgreSQL superuser
createuser -s postgres

# Create a new database named 'chat'
createdb -E UTF8 chat
# dropdb emb

# Connect to the newly created database
psql chat

# Set User Password, execute SQL in command line.
ALTER USER postgres WITH PASSWORD '123456';
```

## Setting Up LLM

You need to set up a local LLM server to provide inference and embedding capabilities. Choose one of the following options:

### Option 1: Ollama

**Use Ollama if you have more than 20GB of memory.** Ollama restricts local PC resources if you have less than 20GB memory (Low VRAM mode).

```sh
# Install Ollama
brew install ollama

# Start server (runs in background)
ollama serve

# Download the model
ollama pull ministral-3:3b

# Show the list of downloaded model
ollama list
```

**Configuration for `.env`:**
```env
LLM_API_BASE_URL=http://127.0.0.1:11434
INFER_MODEL=ministral-3:3b
EMBEDDING_MODEL=ministral-3:3b
```

### Option 2: LlamaCpp (Recommended)

**Recommended for most users.** LlamaCpp efficiently uses available PC resources and inference speed is 2-3 times faster than Ollama.

```sh
# Install LlamaCpp
brew install llama.cpp

# Download and start server in one command
llama-server -hf ggml-org/Ministral-3-3B-Instruct-2512-GGUF \
  --threads-http 1 \
  --temp 0.1 \
  --embeddings \
  --pooling mean

# Check downloaded model location
ls -l ~/Library/Caches/llama.cpp/
```

**Configuration for `.env`:**
```env
LLM_API_BASE_URL=http://127.0.0.1:8080
INFER_MODEL=local
EMBEDDING_MODEL=local
```

**Note:** The server will download the model on first run. Make sure the server is running before using the CLI.


## Setting up project
```sh
# Install dependencies
uv sync

# Set up environment variables
# Create a `.env` file in the project root:
cp .env.sample .env

# Run database migrations
uv run alembic upgrade head

# Set up pre-commit hooks (optional but recommended)
uv run pre-commit install

# Check if the CLI works
uv run cli.py --help
```

## Usage

### Embedding Documents (`emb`)

Embed PDF files into the database for later retrieval. The command processes PDFs by converting each page to images, extracting text via OCR, and storing chunks with embeddings.

```sh
# Embed a single PDF file
uv run cli.py emb /path/to/document.pdf

# Embed all PDFs in a directory
uv run cli.py emb /path/to/documents/

# Embed with custom resolution
uv run cli.py emb /path/to/document.pdf --resolution high

# Interactive mode (will prompt for path)
uv run cli.py emb
```

**Options:**
- `--resolution, -r`: Image resolution for OCR
  - `low`: 50 DPI (faster, lower quality)
  - `middle`: 100 DPI (default, balanced)
  - `high`: 200 DPI (slower, higher quality)

**What it does:**
1. Converts each PDF page to an image
2. Uses LLM to extract markdown text from images
3. Chunks the text into manageable pieces
4. Generates embeddings for each chunk
5. Stores chunks in the database with metadata

### Querying Documents (`infer`)

Ask questions about your embedded documents. The system will find relevant chunks and generate answers based on the content.

```sh
# Ask a question directly
uv run cli.py infer "What is the main topic of the document?"

# Interactive mode (will prompt for question)
uv run cli.py infer
```

**What it does:**
1. Rewrites your question to improve retrieval
2. Generates an embedding for the rewritten question
3. Searches for similar chunks in the database using cosine similarity
4. Uses the retrieved chunks as context
5. Generates an answer based on the relevant content

**Debug mode:**
To see the retrieved chunks and their similarity distances:
```sh
LOG_LEVEL=debug uv run cli.py infer "your question"
```

### Development Commands
```sh
# Format code
uv run fmt

# Lint code
uv run lint

# Run migrations
uv run alembic upgrade head

# Create a new migration
uv run alembic revision --autogenerate -m "description"
```

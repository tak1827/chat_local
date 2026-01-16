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

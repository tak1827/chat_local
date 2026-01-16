# Getting Started
## Setting Up the Database
```sh
# Install PostgreSQL and pgvector extension
brew install postgresql@17 pgvector

# Show status
brew services info postgresql@17

# Start PostgreSQL service
brew services start postgresql@17

# Create a PostgreSQL superuser
createuser -s postgres

# Create a new database named 'chat'
createdb -E UTF8 chat
# dropdb emb

# Connect to the newly created database
psql chat
```

Set User Password
Once connected to psql, run the following SQL command:
```sql
-- Set a password for the 'postgres' user
ALTER USER postgres WITH PASSWORD '123456';
```

**Note:** The pgvector extension will be created automatically when you run migrations:
```sh
# Run migrations (this will create the vector extension automatically)
alembic upgrade head
```

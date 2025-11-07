# Docker Setup Guide

This guide explains how to run the RDMS application using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)

## Quick Start

1. **Create environment file**

   Create a `.env` file in the project root with the following variables:
   ```bash
   # Create .env file
   cat > .env << EOF
   # Database Configuration
   DB_HOST=db
   DB_PORT=5432
   DB_NAME=rdms
   DB_USER=postgres
   DB_PASSWORD=postgres

   # Application Security
   SECRET_KEY=your-secret-key-change-in-production

   # OpenAI Configuration (REQUIRED)
   OPENAI_API_KEY=your-openai-api-key-here

   # LangSmith Configuration (Optional but recommended)
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your-langsmith-api-key-here
   LANGCHAIN_PROJECT=rdms
   EOF
   ```

   Edit `.env` and set the following required variables:
   - `OPENAI_API_KEY` - Your OpenAI API key (required)
   - `LANGCHAIN_API_KEY` - Your LangSmith API key (optional but recommended)
   - `SECRET_KEY` - A secret key for JWT tokens (change in production)
   - Database credentials (defaults are provided)

2. **Build and start services**

   From the project root directory, run:
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```
   
   Or navigate to the docker folder:
   ```bash
   cd docker
   docker-compose up -d
   ```

   This will:
   - Build the application Docker image
   - Start PostgreSQL database
   - Initialize the database schema
   - Start the FastAPI application

3. **Access the application**

   - Web UI: http://localhost:8011
   - API Docs: http://localhost:8011/docs
   - Health Check: http://localhost:8011/health

## Environment Variables

### Required

- `OPENAI_API_KEY` - OpenAI API key for AI features

### Optional (with defaults)

- `DB_HOST` - Database host (default: `db` in Docker)
- `DB_PORT` - Database port (default: `5432`)
- `DB_NAME` - Database name (default: `rdms`)
- `DB_USER` - Database user (default: `postgres`)
- `DB_PASSWORD` - Database password (default: `postgres`)
- `SECRET_KEY` - JWT secret key (default: `your-secret-key-change-in-production`)
- `LANGCHAIN_TRACING_V2` - Enable LangSmith tracing (default: `true`)
- `LANGCHAIN_API_KEY` - LangSmith API key (optional)
- `LANGCHAIN_PROJECT` - LangSmith project name (default: `rdms`)

## Docker Commands

All commands should be run from the project root, or use `-f docker/docker-compose.yml` flag.

### Start services
```bash
# From project root
docker-compose -f docker/docker-compose.yml up -d

# Or from docker folder
cd docker && docker-compose up -d
```

### View logs
```bash
# All services
docker-compose -f docker/docker-compose.yml logs -f

# Specific service
docker-compose -f docker/docker-compose.yml logs -f app
docker-compose -f docker/docker-compose.yml logs -f db
```

### Stop services
```bash
docker-compose -f docker/docker-compose.yml stop
```

### Stop and remove containers
```bash
docker-compose -f docker/docker-compose.yml down
```

### Stop, remove containers, and volumes (⚠️ deletes database data)
```bash
docker-compose -f docker/docker-compose.yml down -v
```

### Rebuild after code changes
```bash
docker-compose -f docker/docker-compose.yml up -d --build
```

### Execute commands in container
```bash
# Access app container shell
docker-compose -f docker/docker-compose.yml exec app bash

# Access database
docker-compose -f docker/docker-compose.yml exec db psql -U postgres -d rdms
```

## Database Setup

The database is automatically initialized with the schema from `sql/0.tables.sql` when the container first starts.

### Load CSV data (optional)

If you want to load the sample CSV data:

```bash
# Copy data files to container
docker cp data/. rdms_app:/app/data/

# Run the data loader script
docker-compose -f docker/docker-compose.yml exec app python scripts/load_csv_to_db.py
```

## Troubleshooting

### Port already in use

If port 8011 or 5432 is already in use, modify the ports in `docker/docker-compose.yml`:

```yaml
ports:
  - "8012:8011"  # Change host port
```

### Database connection errors

1. Ensure the database container is healthy:
   ```bash
   docker-compose -f docker/docker-compose.yml ps
   ```

2. Check database logs:
   ```bash
   docker-compose -f docker/docker-compose.yml logs db
   ```

3. Verify environment variables are set correctly in `.env`

### Application won't start

1. Check application logs:
   ```bash
   docker-compose -f docker/docker-compose.yml logs app
   ```

2. Verify all required environment variables are set (especially `OPENAI_API_KEY`)

3. Rebuild the image:
   ```bash
   docker-compose -f docker/docker-compose.yml up -d --build
   ```

### Token limit not working

The token limit is implemented client-side in the browser. It uses localStorage to track daily usage. If you're testing:

1. Clear browser localStorage to reset the limit
2. Check browser console for any JavaScript errors
3. Ensure the frontend is being served correctly

## Development

For development, you can mount your local code as volumes (already configured in `docker/docker-compose.yml`):

- `./static` - Frontend files (hot-reload on changes)
- `./result` - Results and generated files
- `./data` - CSV data files
- `./documents` - PDF documents for RAG

Changes to these directories will be reflected immediately. For Python code changes, rebuild the container:

```bash
docker-compose -f docker/docker-compose.yml up -d --build
```

## Production Deployment

For production:

1. **Change default credentials** - Update all default passwords and secrets in `.env`
2. **Use secrets management** - Consider using Docker secrets or a secrets manager
3. **Enable HTTPS** - Use a reverse proxy (nginx, Traefik) with SSL certificates
4. **Set resource limits** - Add resource constraints in `docker/docker-compose.yml`
5. **Backup database** - Set up regular database backups
6. **Monitor logs** - Use a logging solution (ELK, Loki, etc.)

Example production `docker/docker-compose.yml` additions:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Architecture

```
┌─────────────┐
│   Browser   │
│  (Port 8011)│
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌─────────────┐
│   FastAPI   │◄────►│ PostgreSQL  │
│   (app)     │      │    (db)     │
└─────────────┘      └─────────────┘
       │
       ▼
┌─────────────┐
│   OpenAI    │
│   LangChain │
└─────────────┘
```

## Support

For issues or questions:
- Check the main [README.md](../README.md)
- Review component-specific documentation:
  - [SQL Generator](../script/sql_generator/README.md)
  - [Customer Chatbot](../script/chatbot/README.md)
  - [Data Engineering](../sql/README.md)


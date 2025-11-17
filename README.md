# Marketmind Scheduler Agent Service

A FastAPI service for scheduling campaigns and posts with intelligent time distribution.

## Features

- Schedule individual posts with timezone conversion
- Schedule entire campaigns with smart post distribution
- Automatic timezone handling using brand defaults
- Database persistence with PostgreSQL
- Naive scheduler (to be replaced with agentic scheduler)

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file by copying the example file:

```bash
cp env.example .env
```

Or create a `.env` file manually with:
```
DATABASE_URL=postgresql+asyncpg://scheduler_user:scheduler_pass@localhost:5432/scheduler_db
POSTGRES_USER=scheduler_user
POSTGRES_PASSWORD=scheduler_pass
POSTGRES_DB=scheduler_db
POSTGRES_PORT=5432
SCHEDULER_PORT=8000
```

**Note:** The docker-compose.yml will use these values, but also has defaults if the `.env` file is not present.

## Running the Service

### Option 1: Using Docker Compose (Recommended)

This will start both the PostgreSQL database and the scheduler service:

```bash
docker-compose up --build
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs

To run in detached mode:
```bash
docker-compose up -d --build
```

To stop the services:
```bash
docker-compose down
```

To stop and remove volumes (clears database):
```bash
docker-compose down -v
```

### Option 2: Local Development

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs

## Database Setup

The service automatically creates database tables on startup. When using Docker Compose, PostgreSQL is automatically configured and started. For local development, ensure PostgreSQL is running and the database exists.

## Scheduling Logic

### Campaign Scheduling
The naive scheduler distributes posts across the campaign period:
- **1 post**: Scheduled on first day at 7 PM (brand timezone)
- **2 posts**: Scheduled on first and last day at 7 PM
- **3+ posts**: First post on first day, last post on last day, remaining posts evenly distributed on days in between, all at 7 PM
- **Validation**: Throws error if number of posts exceeds number of days

### Post Scheduling
- Converts timestamp to UTC using provided timezone (or brand default)
- Creates schedule record with PENDING status
- Generates unique UUID for schedule_id

## Project Structure

```
.
├── main.py              # FastAPI application and endpoints
├── service.py           # Business logic layer
├── models.py            # SQLAlchemy database models
├── database.py          # Database configuration and session management
├── naive_scheduler.py   # Naive scheduling logic (to be replaced with agentic_scheduler)
├── load_dummy_data.py   # Script to load dummy data on startup
└── requirements.txt     # Python dependencies
```

## Database Models

- **Schedule**: Stores post schedules with status, retry count, and publish time
- **Post**: Post information linked to campaigns and brands
- **Campaign**: Campaign details with start/end dates and post count
- **Brand**: Brand information with default timezone

## Future Enhancements

- Replace naive scheduler with agentic scheduler using LLM for intelligent scheduling
- Support for multiple platforms (currently hardcoded to TWITTER)


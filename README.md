# Marketmind Scheduler Agent Service

A FastAPI service for scheduling campaigns and posts with intelligent time distribution.

## Features

- Schedule individual posts with timezone conversion
- Schedule entire campaigns with smart post distribution
- Automatic timezone handling using brand defaults
- Database persistence with PostgreSQL
- Naive scheduler (to be replaced with agentic scheduler)
- Automatic database initialization and dummy data loading on startup

## Prerequisites

- Docker and Docker Compose installed on your system

## Configuration

Create a `.env` file by copying the example file:

```bash
cp env.local .env
```

The `.env` file should contain the following variables:
- `POSTGRES_USER`: PostgreSQL username (default: scheduler_user)
- `POSTGRES_PASSWORD`: PostgreSQL password (default: scheduler_pass)
- `POSTGRES_DB`: PostgreSQL database name (default: scheduler_db)
- `POSTGRES_PORT`: PostgreSQL port (default: 5432)
- `SCHEDULER_PORT`: Scheduler service port (default: 8000)

## Deployment

### Using Docker Compose

This will start both the PostgreSQL database and the scheduler service:

```bash
docker-compose up --build
```

The API will be available at:
- API: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

To run in detached mode:
```bash
docker-compose up -d --build
```

To view logs:
```bash
docker-compose logs -f scheduler
```

To stop the services:
```bash
docker-compose down
```

To stop and remove volumes (clears database):
```bash
docker-compose down -v
```

## Database Setup

The service automatically:
- Creates database tables on startup
- Clears existing tables before initialization
- Loads dummy data for testing

PostgreSQL is automatically configured and started via Docker Compose with health checks to ensure the database is ready before the scheduler service starts.

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

## API Endpoints

### Root
- `GET /` - Service information and available endpoints

### Campaign Scheduling
- `POST /schedule/campaign/{campaign_id}` - Schedule all posts in a campaign
- `GET /schedule/campaign/{campaign_id}` - Get all schedules for a campaign

### Post Scheduling
- `POST /schedule/post/{post_id}` - Schedule a single post with timestamp and timezone
- `GET /schedule/post/{post_id}` - Get the schedule for a post

### Health
- `GET /health` - Health check endpoint

## Project Structure

```
.
├── app.py               # FastAPI application and endpoints
├── service.py           # Business logic layer
├── models.py            # SQLAlchemy database models
├── database.py          # Database configuration and session management
├── naive_scheduler.py   # Naive scheduling logic (to be replaced with agentic_scheduler)
├── load_dummy_data.py   # Script to load dummy data on startup
├── docker-compose.yml   # Docker Compose configuration
├── Dockerfile           # Docker image definition
├── env.local            # Environment variables template
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


# YouTube Video Summarizer

A backend service that processes YouTube links asynchronously to generate accurate, grammar-corrected summaries using **Whisper** and **FLAN-T5** models.
It uses **FastAPI**, **Celery**, **Redis**, and **MongoDB** to handle ML-heavy workloads efficiently through background processing and caching.

---

## Tech Stack
- **FastAPI** – REST API and validation
- **Celery + Redis** – asynchronous task queue and state tracking
- **MongoDB (Motor)** – persistent storage for videos and tasks
- **Whisper** – speech-to-text model
- **FLAN-T5** – transformer model for summarization
- **LanguageTool** – grammar correction
- **yt-dlp + ffmpeg** – audio and captions extraction

---

## Workflow

1. Client sends a YouTube URL to the API.
2. System checks if the url is already queued. (if yes then return the taskID as response)
3. System checks Redis (cache) and MongoDB (database) for existing summaries.
4. If not found, the video is queued in Celery for background processing.
5. The Celery worker:
   - Downloads captions or audio.
   - Runs Whisper → LanguageTool → FLAN-T5.
   - Stores the processed summary in MongoDB and Redis.
6. Client can poll `/status` with a `task_id` to check progress.

---

## Key Features

- Clear separation between layers (`domain`, `application`, `infrastructure`, `presentation`)
- Asynchronous MongoDB and Redis operations
- Automatic Celery retry and task tracking

---

## Setup

### 1. Clone the Repository
```bash
git clone https://github.com/jishnu70/Youtube_video_summarizer.git
cd Youtube_video_summarizer
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
# or
.venv\Scripts\activate     # Windows
```

### 3. Install Dependencies
Using `uv`:
```bash
uv sync
```
Or with `pip`:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create a `.env` file in the project root:

### 5. Start Services
Run MongoDB and Redis locally or via Docker.

```bash
docker run -d -p 6379:6379 redis
docker run -d -p 27017:27017 mongo
```

### 6. Run the FastAPI Server
```bash
uvicorn src.presentation.routes:app --reload
```

### 7. Start Celery Worker
```bash
celery -A src.background.celery_app.celery_app worker --loglevel=info
```

---

## API Endpoints

| Method | Endpoint | Description |
|---------|-----------|-------------|
| `POST` | `/` | Submit YouTube URL for summarization |
| `POST` | `/status?task_id=` | Check task status using `task_id` |
| `GET` | `/` | Health check |

---

## Example Request

```json
POST /
{
  "url": "https://www.youtube.com/watch?v=example123"
}
```

**Response:**
```json
{
  "task_id": "0d47c2e4-24b3-4bfe-8b1b-57b7fda7c44e",
}
```

---

## Next Steps
- Add Docker Compose for local orchestration
- Add tests using `pytest-asyncio`
---

**Author:** Jishnu C

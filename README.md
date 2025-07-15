# AI Agent Quiz Platform

A full-stack FastAPI application that enables users to create, take, and manage quizzes. It supports both user-generated and AI-generated quizzes powered by the Groq API. The platform includes features such as quiz recommendations, a leaderboard, and trending technology tracking.

---

## Features

- User authentication using JWT
- Manual and AI-powered quiz creation
- Quiz attempt tracking and scoring
- Periodic AI agent for automatic quiz generation
- Personalized quiz recommendations
- Leaderboard for top performers
- Tracking of trending technologies

---

## Tech Stack

| Layer       | Technology               |
|-------------|--------------------------|
| Backend     | FastAPI, SQLAlchemy      |
| AI Engine   | Groq API                 |
| Database    | Postgre SQL(Google Cloud)|
| Auth        | OAuth2 with JWT          |
| Deployment  | Render.com               |
| Migrations  | Alembic                  |

---

## Project Structure

```
AI-Agent-Quiz-Platform/
│
├── app/
│   ├── controllers/       # API routers
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic layer
│   ├── utils/             # Utilities, Groq client, migration runner
│
├── alembic/               # Alembic migration scripts
├── main.py                # FastAPI entry point
├── render.yaml            # Render deployment descriptor
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
```

---

## Environment Variables

| Variable Name          | Description                            |
|------------------------|----------------------------------------|
| `DATABASE_URL`         | Connection string to Postgre SQL       |
| `SECRET_KEY`           | Secret key for JWT                     |
| `GROQ_API_KEY`         | API key for Groq quiz generation       |

These are managed in the Render dashboard or a `.env` file locally.

---

## Local Installation

1. **Clone the repository:**

```bash
git clone https://github.com/raghavendrareddy23/AI-Agent-quiz-platform.git
cd AI-Agent-Quiz-Platform
```

2. **Create a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Run migrations (if needed):**

```bash
alembic upgrade head
```

5. **Start the application:**

```bash
uvicorn main:app --reload
```

Access the app at: `https://ai-agent-quiz-platform.onrender.com/docs`

---

---

## API Endpoints

| Method | Endpoint                        | Description                        |
|--------|----------------------------------|------------------------------------|
| POST   | `/api/v1/auth/register`         | Register new user                  |
| POST   | `/api/v1/auth/login`            | Login and receive JWT              |
| GET    | `/api/v1/quiz/public`           | View all public quizzes            |
| GET    | `/api/v1/quiz/user`             | View user-created quizzes          |
| POST   | `/api/v1/quiz/create`           | Create a quiz manually             |
| POST   | `/api/v1/quiz/generate`         | Generate quiz using Groq           |
| POST   | `/api/v1/quiz/submit`           | Submit quiz attempt                |
| GET    | `/api/v1/quiz/users/attempt`    | Get user quiz attempts             |
| GET    | `/api/v1/quiz/{quiz_id}`        | Get quiz details by ID             |
| GET    | `/api/v1/ai/recommendations`    | Personalized quiz recommendations  |
| GET    | `/api/v1/ai/leaderboard`        | Top performers by score            |
| GET    | `/api/v1/ai/trending`           | List trending technologies         |

---

## AI Agent Overview

- Runs automatically in the background every 15 minutes.
- Selects random trending technology and difficulty to generate quizzes.
- Saves quizzes to the database with `created_by = -1` and `is_ai_generated = True`.
- Retries Groq API requests with exponential backoff if necessary.
- Updates trending scores and influences recommendations.

---

## License

This project is licensed under the MIT License.

---

## Author

Developed by Raghavendra Reddy Munagala

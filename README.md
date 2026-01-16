# FastAPI AI Backend

A production-ready FastAPI-based AI backend with authentication, chat history, text summarization, and translation features. The project is fully Dockerized and integrates with Google Gemini for AI capabilities.

## ✨ Features

- **FastAPI + Uvicorn** - Modern, fast web framework
- **JWT Authentication** - Secure user registration, login, password change, and account deletion
- **AI-Powered Chat** - Interactive chat with Google Gemini
- **Chat History Management** - Full CRUD operations for chat history
- **Text Summarization** - AI-powered text summarization
- **Text Translation** - Multi-language translation support
- **Google Gemini API Integration** - Latest AI capabilities
- **SQLite Database** - Persistent storage via Docker volume
- **Alembic Migrations** - Database version control
- **Swagger UI** - Interactive API documentation (OpenAPI)
- **Health Check Endpoint** - Monitor application status
- **Fully Dockerized** - Easy deployment and development

## 📦 Requirements

You only need:

- **Docker** (Docker Desktop recommended)
- **Docker Compose** (included with Docker Desktop)

⚠️ Important: Docker Desktop must be running before you execute any docker or docker compose commands. On Windows and macOS, make sure the Docker Desktop application is open and the Docker engine is started.

No local Python installation or virtual environment is required.

## 🔐 Environment Variables

The application uses environment variables for secrets and configuration.

### Required Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key for AI features |
| `SECRET_KEY` | Secret key for JWT token signing (min. 32 characters) |

## 🔑 Getting Required Keys

### 1. Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Get API Key"** or **"Create API Key"**
4. Select an existing project or create a new one
5. Copy the generated API key
6. Keep this key secure

### 2. Secret Key Generation

You need a secure random string for JWT token signing. Generate one using:

**Option A: Using Python**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Option B: Using OpenSSL**
```bash
openssl rand -hex 32
```

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/berkaykhrmn/fastapi-ai-backend.git
cd fastapi-ai-backend
```

### 2️⃣ Create the .env File

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and provide your own values:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
SECRET_KEY=your_generated_secret_key_here
```

### 3️⃣ Build and Run with Docker

**Start the application:**

```bash
docker compose up --build
```

**View logs:**

```bash
docker compose logs -f
```

**Stop the application:**

```bash
docker compose down
```

**Stop and remove volumes (clears database):**

```bash
docker compose down -v
```

## 🌐 API Access

| URL | Description |
|-----|-------------|
| http://localhost:8000 | Redirects to Swagger UI |
| http://localhost:8000/docs | Swagger UI (Interactive API documentation) |
| http://localhost:8000/redoc | ReDoc (Alternative API documentation) |
| http://localhost:8000/health | Health check endpoint |

## 🔌 API Endpoints

### Authentication

| User Type | Requests per Minute | Time Window |
|-----------|---------------------|-------------|
| **Guest (Unauthenticated)** | 3 requests | 60 seconds |
| **Authenticated User** | 5 requests | 60 seconds |


| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| `POST` | `/auth/register` | Register a new user | No |
| `POST` | `/auth/token` | Authenticate and obtain JWT token | No |
| `PUT` | `/auth/password` | Change user password | Yes |
| `DELETE` | `/auth/delete` | Delete user account | Yes |

### Chat & AI

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| `POST` | `/chat` | Chat with AI | Optional |
| `GET` | `/chat/history` | Retrieve chat history | Yes |
| `DELETE` | `/chat/history/{chat_id}` | Delete specific chat entry | Yes |

### AI Utilities

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| `POST` | `/chat/summarize` | Summarize a given text | Optional |
| `POST` | `/chat/translate` | Translate text to target language | Optional |

### System

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| `GET` | `/health` | API health check | No |


## 🔧 Development

### Running Locally Without Docker

If you prefer to run without Docker:

1. **Install Python 3.11+**
2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set environment variables:**
   ```bash
   export GEMINI_API_KEY="your_key"
   export SECRET_KEY="your_secret"
   ```
5. **Run migrations:**
   ```bash
   alembic upgrade head
   ```
6. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

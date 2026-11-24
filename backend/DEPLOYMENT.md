# EXAMFLOW BACKEND DEPLOYMENT GUIDE (Google Cloud Run & Docker)

## 1. Local Development Setup
```bash
cd backend
python -m venv venv
# On Windows: venv\Scripts\activate | On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```
Swagger UI will be live at `http://localhost:8080/docs`.

## 2. Docker & Docker Compose
From repository root:
```bash
docker compose up --build
```
This starts PostgreSQL 16 on port 5432, FastAPI Backend on port 8080, and proxies frontend requests on port 5173.

## 3. Google Cloud Run Deployment
Deploy container to Cloud Run connected to Cloud SQL:
```bash
gcloud builds submit --tag gcr.io/$PROJECT_ID/examflow-backend ./backend

gcloud run deploy examflow-backend \
    --image gcr.io/$PROJECT_ID/examflow-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars ENVIRONMENT=production,DATABASE_URL="postgresql+asyncpg://examuser:PASSWORD@/examflow?host=/cloudsql/$PROJECT_ID:us-central1:examflow-db" \
    --add-cloudsql-instances $PROJECT_ID:us-central1:examflow-db
```

## 4. Database Migrations
Run Alembic migrations:
```bash
alembic upgrade head
```

## 5. Health Check Endpoint
`GET /health` returns:
```json
{
  "status": "healthy",
  "service": "EXAMFLOW Backend",
  "version": "1.0.0"
}
```

# GoExpressly

A monorepo for the GoExpressly courier platform.

## Architecture

This repository is designed as a monorepo. It currently contains:
- `backend/` — The core logic, admin portal API, and tracking framework built with FastAPI (Python).
- `frontend/` — The customer-facing website and tracking UI built with HTML, Tailwind CSS, and vanilla JS.

---

## Backend (`/backend`)

The backend is a high-performance Python application providing:
- **Admin Management:** Secure authentication and package lifecycle management.
- **Package Tracking:** Database tables tracking status history chronologically.
- **Email Notifications:** Asynchronous background dispatch of emails upon status updates.

### Tech Stack
- **Framework:** FastAPI
- **Database:** PostgreSQL (hosted on Supabase)
- **ORM:** SQLAlchemy
- **Authentication:** JWT (bcrypt for passwords)
- **Emails:** Setup to use SMTP or Resend REST API

### 🚀 Local Development Setup

**1. Navigate to the backend directory:**
```bash
cd backend
```

**2. Set up your Python environment:**
It is highly recommended to use a virtual environment.
```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies:**
```bash
pip install -r requirements-dev.txt
```

**4. Configure Environment Variables:**
Copy the template `.env` and fill it out:
```bash
cp .env.example .env
```
Ensure your `DATABASE_URL` connects to a valid PostgreSQL instance. (Note: If using Supabase, use your **Session pooler** or **Transaction pooler** string on port 6543 to avoid IPv6 connection issues locally).

**5. Seed your database (First run only):**
Once the database is connected, this script creates your database tables automatically and seeds your first admin user.
```bash
python scripts/seed_admin.py
```

**6. Start the server (Development):**
```bash
uvicorn app.main:app --reload --port 8000
```
Open **http://localhost:8000/docs** in your browser to interact with the Swagger API playground!

---

## Frontend (`/frontend`)

The frontend is a lightweight, high-performance static UI utilizing a glassmorphic aesthetic.
- **Tools:** HTML, Vanilla JS (`carousel.js`, `theme.js`, `api.js`), and Tailwind CSS CLI.
- **Design System:** Custom CSS tokens for glass effect, soft shadows, and fully integrated Light/Dark modes based on `prefers-color-scheme`.
- **Assets:** Fully generated imagery, loaded efficiently via WebP/optimized formats. No external dependencies.

### 🚀 Local Development Setup

**1. Navigate to the frontend directory:**
```bash
cd frontend
```

**2. Install dependencies:**
```bash
npm install
```

**3. Run the development CSS compiler:**
Continually watches file changes and recompiles the Tailwind file `dist/css/main.min.css`:
```bash
npm run dev
```

**4. Open the app locally:**
For development, you can simply open `/public/index.html` via Live Server or similar local web servers. Ensure your backend is running on `localhost:8000` (the frontend is configured to target it automatically during dev).

### 🐳 Docker (Production)
A consolidated `docker-compose.yml` file is provided in the **root** folder. It builds both the FastAPI backend and the Nginx frontend reverse-proxy.

```bash
docker compose up --build -d
```
You can access the full frontend on `http://localhost/` and the backend is seamlessly proxied behind `/api/*`.

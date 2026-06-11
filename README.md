# NexFlow AI Backend

AI Assistant Platform for Service-Based Businesses.

## Features
- **Custom User Model:** Admin and Business Owner roles.
- **Onboarding System:** Admin-generated links for business onboarding.
- **AI Assistants:** Hosted assistant pages (API) with custom knowledge bases.
- **Lead & Booking Capture:** Public endpoints for customer inquiries.
- **Production Ready:** Environment variable configuration, Whitenoise, Gunicorn ready.
- **API Documentation:** Swagger and Redoc integrated via `drf-spectacular`.

## Tech Stack
- Django 6.0
- Django REST Framework
- PostgreSQL (ready via `DATABASE_URL`)
- JWT Authentication
- Whitenoise (Static files)

## Setup

1. **Clone the repository.**
2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Create a `.env` file:**
   ```env
   DEBUG=True
   SECRET_KEY=your-secret-key
   DATABASE_URL=sqlite:///db.sqlite3  # Use postgres://user:password@host:port/db for production
   ALLOWED_HOSTS=localhost,127.0.0.1
   CORS_ALLOWED_ORIGINS=http://localhost:3000
   ```
5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```
6. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```
7. **Run the server:**
   ```bash
   python manage.py runserver
   ```

## API Documentation
- Swagger UI: `/api/schema/swagger-ui/`
- Redoc: `/api/schema/redoc/`

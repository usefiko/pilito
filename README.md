# Pilito-Backend
## Resolve customer requests instantly with AI customer service. 


[![](https://img.shields.io/badge/Python-3.12.4-orange)](https://www.python.org/)
[![](https://img.shields.io/badge/Django-5.2.1-green)](https://www.djangoproject.com/)


## 🐍 Django Dockerized Project 
This project is a Django application containerized with Docker, using PostgreSQL as the database and Redis for caching or async task queuing. The Django source code is located inside the `src/` directory.

---


## 🚀 Features

- Django 5+ (inside `src/`)
- PostgreSQL 15
- Redis 7
- Docker & Docker Compose
- Environment-based settings
- Volume persistence for database, media, and static files

---

## 📁 Project Structure

```
.
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── .env
├── README.md
└── src/
    ├── manage.py
    ├── core/
    └── accounts/
    ...
```

---

## 🧩 Requirements

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/usefiko/pilito.git
cd Fiko-Backend
```

### 2. Create your `.env` file

```env
# .env
STAGE="DEV"
DEBUG=True
SECRET_KEY=your_secret_key
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
POSTGRES_DB=your_db_name
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=db
POSTGRES_PORT=5432
CSRF_TRUSTED_ORIGINS=""
CSRF_COOKIE_DOMAIN=""
STATIC_URL=""
MEDIA_URL=""
REDIS_URL=redis://redis:6379/0
```

### 3. Build and run with Docker

```bash
docker-compose build
docker-compose up
```

This will:
- Build the Django app
- Run `migrate` and `collectstatic` automatically
- Start the app on `http://localhost:8000`

---

## 📦 Useful Commands

### Rebuild containers

```bash
docker-compose up --build
```

### Run a command inside the web container

```bash
docker-compose exec web python manage.py createsuperuser
```
### For Docker Desktop (macOS/Windows)

```bash
docker compose exec web python manage.py createsuperuser
```

### Or Using docker exec

```bash
docker exec -it <container_name> python manage.py makemigrations
docker exec -it <container_name> python manage.py migrate
```


---

## 🗂️ Volumes

- `postgres_data`: Stores PostgreSQL database data
- `static_volume`: For Django `collectstatic` output
- `media_volume`: For user uploads

---


```bash
docker-compose up -d --build
```

### Check if you're using Docker Desktop (macOS/Windows)
```bash
docker compose build
docker compose up --build
```

 enjoy!
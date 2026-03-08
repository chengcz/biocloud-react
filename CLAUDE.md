# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A dockerized full-stack CRUD application with FastAPI backend, PostgreSQL database, and React (Vite) frontend. The app demonstrates a drag-and-drop card interface that polls the backend for changes.

## Running the Project

```bash
docker-compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Adminer (DB admin): http://localhost:8080
- PostgreSQL: localhost:5432 (user: `username`, pass: `password`, db: `vector`)

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│  PostgreSQL │
│  (Vite/React│     │  (FastAPI)  │     │             │
│   :5173)    │     │   (:8000)   │     │   (:5432)   │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Backend (`backend/src/`)

- **api.py** - FastAPI routes for CRUD operations on `Item` model
- **models.py** - SQLAlchemy ORM model (`Item` with type, title, position)
- **db.py** - Database connection and session setup
- **seed.py** - Initial data for development

### Frontend (`frontend/src/`)

- **App.jsx** - Main React component with drag-and-drop (react-beautiful-dnd) and polling
- Vite proxies `/api/*` requests to backend via `host.docker.internal:8000`

### Database

- PostgreSQL with SQLAlchemy ORM
- Single table `items` (position as primary key, type, title)
- Schema created on startup via `models.Base.metadata.create_all()`

## Development Notes

- Backend uses a global `SessionLocal` instance (not per-request sessions)
- Frontend polls `/api/items` every 10 seconds for changes
- Backend runs with `--reload` for hot reloading in Docker
- Frontend volume mounts exclude `node_modules` for host development

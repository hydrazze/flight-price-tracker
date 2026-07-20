# ✈️ Flight Price Tracker

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Aiogram](https://img.shields.io/badge/Aiogram-3-2CA5E0)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED)
![License](https://img.shields.io/badge/license-MIT-green)

A Telegram bot for automatically tracking flight ticket prices.

---

## 📋 Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [ER Diagram](#-er-diagram)
- [Requirements](#-requirements)
- [Environment Variables](#-environment-variables)
- [Bot Commands](#-bot-commands)
- [Local Setup](#-local-setup)
- [Running with Docker](#-running-with-docker)
- [Database Migrations](#-database-migrations)
- [Testing](#-testing)
- [License](#-license)

---

## ✨ Features

- ✈️ Create flight price tracking
- 💰 Track price changes
- 🎯 Notifications when a target price is reached
- 📉 Notifications on any price change
- 📊 Price change history
- 📦 Automatic archiving of completed trackings
- 🔄 Manual price check
- ⏰ Automatic scheduled price checks

---

## 🛠 Tech Stack


|
 Technology 
|
 Purpose 
|
---
|
 Python 3.13 
|
 Implementation language 
|
|
 Aiogram 3 
|
 Telegram Bot API framework 
|
|
 SQLAlchemy 2 
|
 ORM 
|
|
 PostgreSQL 
|
 Database 
|
|
 Alembic 
|
 Database migrations 
|
|
 HTTPX 
|
 Async HTTP requests to the price provider 
|
|
 Pydantic Settings 
|
 Configuration management 
|
|
 Docker / Docker Compose 
|
 Containerization and local environment 
|

---

## 🏗 Architecture

Telegram  
    │  
    ▼  
Aiogram Handlers ──▶ Middlewares  
    │  
    ▼  
Services  
    │  
    ▼  
Repositories  
    │  
    ▼  
PostgreSQL  

Scheduler ──▶ Services (periodic price checks)
Providers ──▶ external flight price API (Travelpayouts)


---

## 📁 Project Structure

app/  
├── config/ # application settings (Pydantic Settings)  
├── database/ # DB connection, sessions  
├── handlers/ # Aiogram handlers  
├── keyboards/ # inline/reply keyboards  
├── logging/ # logging configuration  
├── middlewares/ # Aiogram middlewares  
├── models/ # SQLAlchemy models  
├── providers/ # external API integrations (Travelpayouts)  
├── repositories/ # data access layer  
├── scheduler/ # background jobs (scheduled price checks)  
├── schemas/ # Pydantic schemas  
├── services/ # business logic  
├── states/ # FSM states  
├── tests/ # tests  
└── utils/ # helper utilities  


---

## 🗄 ER Diagram

<a href="assets/db_schema.svg">
  <img src="assets/db_schema.svg" width="750">
</a>

---

## ✅ Requirements

- Python 3.13+
- PostgreSQL 14+
- [uv](https://docs.astral.sh/uv/) — package and virtual environment manager
- Docker and Docker Compose (for containerized setup)
- A Telegram bot token (get one from [@BotFather](https://t.me/BotFather))
- A [Travelpayouts](https://www.travelpayouts.com/) API key for fetching flight prices

---

## ⚙️ Environment Variables

Create a `.env` file based on `.env.example`:

| Variable | Description | Example |
|---|---|---|
| `BOT_TOKEN` | Telegram bot token from BotFather | `123456789:AAExampleTokenHere` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:password@localhost:5432/flight_tracker` |
| `TRAVELPAYOUTS_API_KEY` | Travelpayouts API key | `your_api_key` |
| `PRICE_CHECK_INTERVAL` | Automatic price check interval, in seconds | `3600` |

---

## 🤖 Bot Commands

| Command | Description |
|---|---|
| **General** | |
| `/start` | Start the bot |
| `/help` | Show all available commands |
| **Tracking** | |
| `/track` | Start tracking a flight |
| `/tracks` | View your tracked flights |
| `/archive` | View trip history |
---

## 🚀 Local Setup

1. Clone the repository:
```bash

git clone https://github.com/hydrazze/flight-price-tracker.git
cd flight-price-tracker
```

2. Install dependencies:
```bash
uv sync
```

3. Fill in `.env` based on `.env.example`.

4. Apply database migrations:
```bash
uv run alembic upgrade head
```

5. Run the bot:
```bash
uv run python -m app.main
```

---

## 🐳 Running with Docker

Build the containers:
```bash
docker compose build
```

Start:
```bash
docker compose up
```
or in detached mode:
```bash
docker compose up -d
```

Stop:
```bash
docker compose down
```

> On first launch, make sure migrations have been applied (see [Database Migrations](#-database-migrations)).

---

## 🔄 Database Migrations

Create a new migration after changing models:
```bash
uv run alembic revision --autogenerate -m "description of changes"
```

Apply migrations:
```bash
uv run alembic upgrade head
```

---

## 🧪 Testing

```bash
uv run pytest
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

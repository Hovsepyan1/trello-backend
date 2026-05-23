# Internship Project: Kanban Board API

A robust RESTful API built with **FastAPI** and **SQLAlchemy** for managing Kanban-style project boards. This project focuses on high-security standards and efficient database transactions.

## 🚀 Features

- **Advanced Authentication:** - Dual-token system: Short-lived **Access Tokens** and long-lived **Refresh Tokens**.
  - **Token Rotation:** Every refresh generates a new pair and invalidates the old one in the database.
  - **Secure Session Management:** Separate storage for refresh tokens to support multiple device logins and easy revocation.
- **Kanban Management:**
  - Dynamic **Boards**, **Sections**, and **Tickets**.
  - Ownership logic: Only board owners or ticket creators can modify specific items.
- **Atomic Database Operations:** - Uses `db.flush()` and single-transaction commits to ensure data integrity (e.g., creating a board and its owner record simultaneously).
- **Relational Integrity:** - Automated cascades to clean up tokens and boards when a user is deleted.

## 🛠 Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL with `asyncpg` (Asynchronous)
- **ORM:** SQLAlchemy 2.0 (Mapped/Declarative style)
- **Migrations:** Alembic
- **Security:** Passlib (bcrypt), PyJWT/python-jose

## ⚙️ Setup & Installation

1. **Clone & Environment:**
   ```bash
   git clone [https://gitlab.com/hnersesyan1/internship_project.git](https://gitlab.com/hnersesyan1/internship_project.git)
   cd internship_project

2. **Configuration:**
Create a .env file based on the following template:
    ```bash
    DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
    SECRET_KEY=your_random_secret_key
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    REFRESH_TOKEN_EXPIRE_MINUTES=10080

3. **Install Dependencies:**
    ```bash
    uv sync  # If using 'uv'
    # OR
    pip install -r requirements.txt

4. **Initialize Database:**
    ```bash
    uv run alembic upgrade head
    
🔐 Authentication Flow
Login: User provides credentials via /users/login. The server creates a session record in the refresh_tokens table and returns both tokens.

Access: The client includes the Access Token in the Authorization: Bearer header for API calls.

Expiry: Once the Access Token expires (e.g., 30 mins), the client calls /users/refresh with the Refresh Token.

Rotation: The server verifies the token against the DB, deletes the used row, and issues a brand-new set of tokens.

🏗 Database Schema Detail
Users: Stores profile and password hashes.

Refresh_tokens: Manages active sessions (user_id, token, expires_at).

Boards: Main project container.

Sections: Groups within a board (Columns).

Tickets: Individual tasks.

Boards_members: Association table with role metadata (e.g., "Owner", "Member").

📖 Development Commands
Start Development Server: 
    uvicorn main:app --reload

Create Migration: 
    alembic revision --autogenerate -m "description"

Apply Migration: 
    alembic upgrade head

Revert Migration: 
    alembic downgrade -1
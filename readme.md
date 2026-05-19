# E-bookstore Backend: A FastAPI Store API for Digital Book Commerce

## A simple, secure online bookstore backend for managing books, users, orders, and reviews MVP (Minimum Viable Product)

E-bookstore is a backend API project built with FastAPI and PostgreSQL that powers an online store for digital books. It provides endpoints for browsing books, creating users, placing orders, commenting, liking, and managing the full purchase workflow. This project is designed for developers who want a production-ready bookstore service with authentication, validation, and an easy path to run locally or contribute.

## What this project does

E-bookstore offers a ready-made REST API for a digital book marketplace. Users can register, log in, browse book listings, place orders, add shipping addresses, post comments, and like book reviews. The API also includes support for order items, category data, user role, and persistence through SQLAlchemy, making it useful for anyone building a storefront or learning how e-commerce backends are structured.

## Architecture overview

The project implements a clean API backend with FastAPI and SQLAlchemy, supported by PostgreSQL for data storage. The main request flow is:

- Client request -> FastAPI route handlers
- Authentication and validation -> business logic
- SQLAlchemy database models -> PostgreSQL persistence
- JSON response -> client

```text
Client -> FastAPI routes -> service logic -> SQLAlchemy models -> PostgreSQL database
```

## API Map: Core Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/users` | Register a new user | No |
| POST | `/login` | Log in / Get JWT Token | No |
| GET | `/books` | List and filter digital books | No |
| GET | `/books/{id}` | Get book details by ID | No |
| POST | `/book/comments` | Create a comment on a book | Yes |
| POST | `/book/likes` | Like or unlike a book | Yes |
| POST | `/order` | Place a new order | Yes |
| GET | `/order/me` | Get user's orders | Yes |
| GET | `/order/{id}` | Get order details | Yes |
| PUT | `/order/{id}/payment` | Complete order payment | Yes |
| POST | `/orderitems` | Add item to order | Yes |
| PUT | `/orderitems/{id}` | Update order item quantity | Yes |
| DELETE | `/orderitems/{id}` | Remove item from order | Yes |
| GET | `/users/me` | Get current user profile | Yes |

For detailed API documentation and admin endpoints, start the server and visit:

```text
http://127.0.0.1:8000/docs
```

## Installation and usage (end-user)

1. Clone the repository or download the source.
2. Create and activate a Python virtual environment.
3. Install dependencies:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

4. Set up the database and environment variables as required for `app.config`.
5. Run the application:

```bash
uvicorn app.main:app --reload
```

6. Open the API documentation in your browser:

```text
http://127.0.0.1:8000/docs
```

The API is now available for end users and clients to interact with the bookstore backend.

## Installation and usage (contributors)

If you want to contribute or run the project in development mode:

1. Fork the repo and clone your fork.
2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Optionally install the project in editable mode for local development:

```bash
pip install -e .
```

4. Initialize the database using PostgreSQL and configure `.env` or environment variables for database connection.
5. Apply migrations if needed:

```bash
alembic upgrade head
```

5. Run tests during development:

```bash
pytest
```

6. Start the development server:

```bash
uvicorn app.main:app --reload
```

This workflow makes it easy to iterate on the API, add features, and verify behavior with automated tests.

## Contributor expectations

Contributions are welcome. To keep the project healthy:

- Open an issue before working on larger changes.
- Create a branch for each feature or fix.
- Keep commits focused and descriptive.
- Submit pull requests with a clear summary.
- Run `pytest` and ensure tests pass before proposing changes.
- Follow project style and existing patterns in `app/`.

## Known issues
- Some endpoints may require additional validation or error handling.
- Missing Docker Support: working on this soon
- The current project is focused on backend API functionality and does not include a frontend UI.

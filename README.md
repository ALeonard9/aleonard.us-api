[![Pylint](https://github.com/ALeonard9/aleonard.us-api/actions/workflows/lint.yaml/badge.svg?branch=main)](https://github.com/ALeonard9/aleonard.us-api/actions/workflows/lint.yaml)
[![Pytest](https://github.com/ALeonard9/aleonard.us-api/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/ALeonard9/aleonard.us-api/actions/workflows/test.yaml)
[![Snyk SCA & SAST](https://github.com/ALeonard9/aleonard.us-api/actions/workflows/security.yaml/badge.svg?branch=main)](https://github.com/ALeonard9/aleonard.us-api/actions/workflows/security.yaml)

# aleonard.us-api

Source code for aleonard.us API

## Overview

Welcome to the **aleonard.us-api** repository! This project provides a robust and scalable API for managing users, built with FastAPI and SQLAlchemy. The API supports user creation, retrieval, updating, and deletion with comprehensive validation and error handling.

## Features

- **User Management**: Create, retrieve, update, and delete users.
- **Authentication**: Secure endpoints with JWT-based authentication.
- **Data Validation**: Ensure data integrity with Pydantic models.
- **Testing**: Comprehensive test suite using pytest.
- **Documentation**: Automatic API documentation with Swagger UI.

## Technology Stack

- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/)
- **Database**: PostgreSQL (or another as specified)
- **Authentication**: JWT (JSON Web Tokens)
- **Testing**: [pytest](https://docs.pytest.org/en/stable/)
- **Others**: Pydantic, Alembic for migrations, etc.

## Installation

### Prerequisites

- **Python**: 3.12 or higher
- **pip**: Package installer for Python
- **virtualenv**: (optional but recommended)

### Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/ALeonard9/aleonard.us-api.git
   cd aleonard.us-api

   ```

2. **Create Virtual Environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate

   ```

3. **Install Dependencies**

### Production Dependencies

```bash
pip install -r requirements/base.txt
```

### Development Dependencies

```bash
pip install -r requirements/dev.txt
```

### Testing Dependencies

```bash
pip install -r requirements/test.txt
```

4. **Set Environment Variables**

   Create a `.env` file in the root directory and add the following:

   ```plaintext
    LZ=<your landing zone>
    ENV=dev
    LOG_LEVEL=INFO
    JWT_SECRET_KEY=<your secret key>
    ADMIN_DISPLAY_NAME=<your display name>
    ADMIN_PASSWORD=<your api password>
    ADMIN_EMAIL=<your email>
    COMPOSE_PROJECT_NAME=phoenix_dev
    POSTGRES_USER=functional_data_api_dev
    POSTGRES_PASSWORD=<your database password>
    POSTGRES_HOST=m3_phoenix_db_dev
    POSTGRES_DB=phoenix
    POSTGRES_EXPOSED_PORT=5430
    POSTGRES_PORT=5432
    POSTGRES_CONNECTION_PORT=5432
    LOKI_URL=http://loki:3100
   ```

5. **Run Migrations**

   Apply database migrations using Alembic to set up the database schema:

   ```bash
   alembic upgrade head
   ```

6. **Run the Application**

   Start the FastAPI application:

   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`.

7. **Access the API Documnentation**

   Open your browser and go to `http://localhost:8000/docs` to view the Swagger UI documentation.

## Testing

Ensure that you have a test database set up in your `.env` file. The test database should have the same schema as the development database.

Run the following command to execute the test suite:

```bash
pytest
```

## Pre-commit Hooks

This repository uses pre-commit hooks to automatically enforce code quality:

- **Linting and Styling**: Tools like `pylint` and `black` ensure consistent styling.
- **Consistency Checks**: Configuration checks help maintain best practices.

## Continuous Integration and Security

Our CI pipeline leverages GitHub Actions to ensure code quality and security:

- **Testing**: Automated tests are run on every push and pull request.
- **Security Scans**:
  - Snyk SCA Scan: Scans for vulnerabilities in dependencies.
  - Snyk SAST Scan: Scans for vulnerabilities in the codebase.
  - CodeQL: Provides secret scanning and vulnerability detection.

## Contributing

Contributions are welcome. Please fork the repository and submit a pull request.

## License

This project is open source and available under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for more information.

```

```

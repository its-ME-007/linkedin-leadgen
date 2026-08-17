from pathlib import Path

PROJECT_NAME = "contact-discovery"

DIRECTORIES = [
    "app",
    "app/database",
    "app/services",
    "app/api",
    "tests",
]

FILES = [
    "app/__init__.py",
    "app/main.py",
    "app/database/__init__.py",
    "app/database/connection.py",
    "app/database/repository.py",
    "app/database/schema.sql",
    "app/services/__init__.py",
    "app/services/jobs.py",
    "app/services/people.py",
    "app/services/contacts.py",
    "app/services/crawler.py",
    "app/api/__init__.py",
    "app/api/routes.py",
    "tests/__init__.py",
    "init_db.py",
    "requirements.txt",
    ".gitignore",
    "README.md",
]


def initialize_project():
    root = Path(PROJECT_NAME)

    for directory in DIRECTORIES:
        (root / directory).mkdir(parents=True, exist_ok=True)

    for file in FILES:
        path = root / file
        if not path.exists():
            path.touch()

    print(f"Project initialized successfully: {root.resolve()}")


if __name__ == "__main__":
    initialize_project()

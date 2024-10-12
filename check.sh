DIRS_WITH_CODE="src test"

# Type hints
echo "Mypy:"
poetry run mypy $DIRS_WITH_CODE

# Linting and formatting
echo "Ruff:"
poetry run ruff check --fix
poetry run ruff format

# Unit tests
echo "Pytest:"
poetry run pytest

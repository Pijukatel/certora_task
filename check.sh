DIRS_WITH_CODE="src test"

# Type hints
echo "Mypy:"
poetry run mypy $DIRS_WITH_CODE

# Formatting and linting
echo "Ruff:"
poetry run ruff check $DIRS_WITH_CODE

# Unit tests
echo "Pytest:"
poetry run pytest

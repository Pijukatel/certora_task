FROM python:3.12-alpine3.20

# Pipx for running code tools
RUN python -m pip install pipx
# Due to issue on Alpine image "pipx ensurepath" will not work.
ENV PATH="/root/.local/bin:$PATH"

# Install poetry
RUN pipx install poetry

# Copy relevant poetry project files
#COPY poetry.lock pyproject.toml .
COPY . /certora_task

# Set up poetry environment
RUN cd certora_task && poetry install --no-root


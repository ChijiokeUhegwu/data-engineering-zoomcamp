# base Docker image that we will build on
FROM python:3.13.11-slim

# Copy uv binary from official uv image (multi-stage build pattern)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# set up the working directory inside the container
WORKDIR /code

# Add virtual environment to PATH so we can use installed packages
ENV PATH="/code/.venv/bin:$PATH"

# Copy dependency files first (better layer caching)
COPY "pyproject.toml" "uv.lock" ".python-version" ./

# Install dependencies from lock file (ensures reproducible builds)
RUN uv sync --locked

# copy the script to the container. 1st name is source file, 
# the . (current working directory) is destination
COPY ingest_data.py .

# define what to do first when the container runs
# In this case, just run the script
ENTRYPOINT ["python", "ingest_data.py"]

# before building a docker image, ensure to always save the dockerfile
# and confirm its content with cat Dockerfile
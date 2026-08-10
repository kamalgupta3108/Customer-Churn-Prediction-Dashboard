# Dockerfile (backend)
# ----------------------
# This file is a step-by-step RECIPE for building a container that has
# everything our FastAPI backend needs to run - Python, our dependencies,
# and our code - packaged together so it runs identically anywhere.

# Start from an official, pre-built Python image (not from scratch) -
# "slim" is a smaller version with just the essentials, keeping our final
# container leaner and faster to build/download.
FROM python:3.11-slim

# Set the "working directory" inside the container - like doing `cd /app`
# before running any commands below. Everything happens relative to here.
WORKDIR /app

# Copy ONLY the requirements file first (not all our code yet) - this is
# a deliberate ordering trick. Docker caches each step; if requirements.txt
# hasn't changed, Docker reuses the cached "pip install" step instead of
# re-running it every single build, even if our actual code changed. This
# can save minutes on every rebuild during development.
COPY requirements.txt .

# --no-cache-dir keeps the image smaller by not storing pip's download
# cache inside the container (we don't need it after install is done).
RUN pip install --no-cache-dir -r requirements.txt

# NOW copy the rest of our actual application code into the container.
COPY api/ ./api/
COPY train.py .
COPY data/ ./data/
COPY model/ ./model/

# Document which port this container listens on (informational - doesn't
# actually publish the port, that happens in docker-compose.yml or `docker run -p`)
EXPOSE 8000

# The actual command that runs when the container starts.
# --host 0.0.0.0 is important: it means "accept connections from outside
# this container," not just from localhost INSIDE the container - without
# this, nothing outside the container could ever reach our API.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

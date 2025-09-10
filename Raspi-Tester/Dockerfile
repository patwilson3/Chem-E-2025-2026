FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install smbus dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    python3-smbus \
    libi2c-dev \
    i2c-tools \
 && rm -rf /var/lib/apt/lists/*

 # Create app directory
WORKDIR /app

# Copy your project
COPY . /app

# Optional: install project as a package
RUN pip install --upgrade pip && pip install -e ./tester

CMD [ "bash" ]
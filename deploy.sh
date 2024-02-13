#!/bin/bash

# Constants definition
REPO_URL="https://github.com/sdkinfotech/moex_alerts.git"
CLONE_PATH="/root/sources/moex_alerts"
IMAGE_TAG="moex_alerts:compose_0.1.0"

# Navigate to the specified directory
cd /root/sources || exit

# Clone the repository
if [ -d "$CLONE_PATH" ]; then
    echo "The directory already exists, updating the repository"
    cd "$CLONE_PATH" || exit
    git pull
else
    echo "Cloning the repository $REPO_URL"
    git clone "$REPO_URL"
    cd "$CLONE_PATH" || exit
fi

# Build the Docker image
echo "Building the Docker image $IMAGE_TAG"
docker build -t "$IMAGE_TAG" .

# Start Docker Compose
echo "Starting Docker Compose"
docker-compose up -d --force-recreate

echo "Script execution completed."
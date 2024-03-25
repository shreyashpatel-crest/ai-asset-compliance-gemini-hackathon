#!/bin/bash

# Set your Git repository URL
GIT_REPO="https://github.com/shreyashpatel-crest/ai-asset-compliance.git"

# Set the branch or tag you want to pull
GIT_BRANCH="develop"

# Set your Docker Compose file path
DOCKER_COMPOSE_FILE="/home/ubuntu/gemini_hackathon_app/ai-asset-compliance/docker-compose.yml"
FILE_TO_REMOVE="/home/ubuntu/gemini_hackathon_app/ai-asset-compliance/data/chat_data.json"

# Set any additional Docker Compose options
DOCKER_COMPOSE_OPTIONS="--detach"  # Use "--detach" to run containers in the background


git checkout $GIT_BRANCH
git pull

# Remove the specified file
echo "Removing the file: $FILE_TO_REMOVE..."
rm -f $FILE_TO_REMOVE
echo "File removed."

# Build and run with Docker Compose
echo "Building and running with Docker Compose..."
docker compose -f $DOCKER_COMPOSE_FILE build
docker compose -f $DOCKER_COMPOSE_FILE up $DOCKER_COMPOSE_OPTIONS


echo "Deployment complete!"

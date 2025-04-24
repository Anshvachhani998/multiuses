#!/bin/bash

# Folder Name
DIR="URL-UPLOADER"

# Check if the folder exists
if [ -d "$DIR" ]; then
    echo "📂 $DIR found. Entering directory..."
    cd $DIR || exit 1
else
    echo "❌ $DIR not found! Running commands in the current directory..."
fi

# Pull the latest updates
echo "🔄 Updating repository..."
git pull https://github.com/Anshvachhani998/URL-UPLOADER

# Restart Docker Container
echo "🚀 Restarting UploaderDL Docker container..."
docker restart UploaderDL

echo "✅ Update & Restart Completed!"

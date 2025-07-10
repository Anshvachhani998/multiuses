#!/bin/bash

# Folder Name
DIR="multiuses"

# GitHub Token
TOKEN="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"

# Check if the folder exists
if [ -d "$DIR" ]; then
    echo "📂 $DIR found. Entering directory..."
    cd $DIR || exit 1
else
    echo "❌ $DIR not found! Running commands in the current directory..."
fi

# Pull the latest updates
echo "🔄 Updating repository..."
git pull https://$TOKEN@github.com/Anshvachhani998/multiuses

# Restart Docker Container
echo "🚀 Restarting multiuses Docker container..."
docker restart multiuses

echo "✅ Update & Restart Completed!"

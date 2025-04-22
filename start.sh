#!/bin/bash

# Folder Name
DIR="TeraBoxDL"

# Check if the folder exists
if [ -d "$DIR" ]; then
    echo "📂 $DIR found. Entering directory..."
    cd $DIR || exit 1
else
    echo "❌ $DIR not found! Running commands in the current directory..."
fi

# Pull the latest updates
echo "🔄 Updating repository..."
sudo git pull https://Anshvachhani998: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@github.com/Anshvachhani998/TeraBoxDL.git

# Restart Docker Container
echo "🚀 Restarting YouTubeDL Docker container..."
sudo docker restart TeraBoxDL

echo "✅ Update & Restart Completed!"

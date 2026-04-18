#!/bin/bash

# GitHub Setup Script for Telegram Bot
# Run this script after configuring your GitHub credentials

echo "=== GitHub Repository Setup ==="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: Git is not installed. Please install git first."
    exit 1
fi

# Set git configuration
read -p "Enter your GitHub username: " GITHUB_USERNAME
read -p "Enter your GitHub email: " GITHUB_EMAIL

git config --global user.name "$GITHUB_USERNAME"
git config --global user.email "$GITHUB_EMAIL"

echo "Git configuration set:"
echo "  Username: $GITHUB_USERNAME"
echo "  Email: $GITHUB_EMAIL"

# Commit changes
echo ""
echo "Committing files..."
git add .
git commit -m "Initial commit: Telegram bot for Dawateislami India with fps.ms deployment support"

if [ $? -eq 0 ]; then
    echo "✓ Files committed successfully"
else
    echo "✗ Failed to commit files"
    exit 1
fi

echo ""
echo "=== Next Steps ==="
echo ""
echo "1. Create a new repository on GitHub:"
echo "   - Go to https://github.com/new"
echo "   - Repository name: telegram-bot"
echo "   - Keep it public or private as you prefer"
echo "   - DO NOT initialize with README, .gitignore, or license"
echo ""
echo "2. After creating the repository, run these commands:"
echo ""
echo "   # Add remote origin"
echo "   git remote add origin https://github.com/$GITHUB_USERNAME/telegram-bot.git"
echo ""
echo "   # Rename main branch if needed"
echo "   git branch -M main"
echo ""
echo "   # Push to GitHub"
echo "   git push -u origin main"
echo ""
echo "3. For fps.ms deployment:"
echo "   - Clone the repository on your fps.ms server:"
echo "     git clone https://github.com/$GITHUB_USERNAME/telegram-bot.git"
echo "   - Follow the deployment guide in DEPLOYMENT_GUIDE.md"
echo ""
echo "Alternative: Use GitHub CLI (if installed)"
echo "   gh repo create telegram-bot --public --source=. --remote=origin --push"
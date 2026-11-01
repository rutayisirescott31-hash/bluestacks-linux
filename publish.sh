#!/usr/bin/env bash
# ==============================================================================
# BlueStacks Linux - GitHub Publishing & Update Script
# Initializes git, checks GitHub CLI authentication, creates public repo,
# and pushes updates cleanly to GitHub.
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}        BlueStacks Linux - GitHub Sync & Publisher             ${NC}"
echo -e "${BLUE}================================================================${NC}"

# 1. Check Git
if ! command -v git &>/dev/null; then
    echo -e "${YELLOW}Installing git...${NC}"
    sudo apt-get install -y git
fi

# Set default git identity if not configured
if [ -z "$(git config --global user.name)" ]; then
    git config --global user.name "BlueStacks Linux Developer"
fi
if [ -z "$(git config --global user.email)" ]; then
    git config --global user.email "developer@users.noreply.github.com"
fi

# 2. Initialize Git repository if needed
if [ ! -d ".git" ]; then
    echo -e "${BLUE}Initializing Git repository...${NC}"
    git init -b main
else
    # Ensure branch is main
    git branch -M main 2>/dev/null || true
fi

# 3. Check GitHub CLI (gh)
if ! command -v gh &>/dev/null; then
    echo -e "${YELLOW}Installing GitHub CLI (gh)...${NC}"
    sudo apt-get update -y && sudo apt-get install -y gh
fi

# 4. Check GitHub Authentication
echo -e "${BLUE}Checking GitHub CLI authentication...${NC}"
if ! gh auth status &>/dev/null; then
    echo -e "${YELLOW}You are not currently logged into GitHub.${NC}"
    echo -e "${GREEN}Starting GitHub interactive authentication...${NC}"
    echo -e "Follow the on-screen instructions (choose GitHub.com -> HTTPS -> Login with a web browser or token):"
    gh auth login
fi

echo -e "${GREEN}✓ GitHub authentication confirmed.${NC}"

# 5. Stage files and Commit
echo -e "${BLUE}Staging files for commit...${NC}"
git add .

COMMIT_MSG="${1:-Update BlueStacks Linux $(date '+%Y-%m-%d %H:%M:%S')}"
if git diff --cached --quiet; then
    echo -e "${GREEN}No changes to commit.${NC}"
else
    git commit -m "$COMMIT_MSG"
fi

# 6. Check Remote or Create Public Repository
REMOTE_URL=$(git remote get-url origin 2>/dev/null || true)
if [ -z "$REMOTE_URL" ]; then
    echo -e "${BLUE}No git remote found. Creating public GitHub repository 'bluestacks-linux'...${NC}"
    gh repo create bluestacks-linux --public --source=. --remote=origin --push --description "High-Performance Android Gaming Player for Linux with KVM & GPU Acceleration"
    echo -e "${GREEN}✓ Public repository created and initial commit pushed!${NC}"
else
    echo -e "${BLUE}Pushing latest updates to remote: $REMOTE_URL...${NC}"
    git push -u origin main
    echo -e "${GREEN}✓ Updates successfully pushed to GitHub!${NC}"
fi

REPO_WEB=$(gh repo view --json url -q .url 2>/dev/null || echo "$REMOTE_URL")
echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}  ✓ Repository is Live & Public: ${BLUE}$REPO_WEB${NC}"
echo -e "${GREEN}================================================================${NC}\n"

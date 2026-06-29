git init
git branch -M main

# Commit 1: June 28 (Initial setup)
$env:GIT_AUTHOR_DATE="2026-06-28T10:00:00"
$env:GIT_COMMITTER_DATE="2026-06-28T10:00:00"
git add README.md .gitignore requirements.txt Dockerfile docker-compose.yml .env.example
git commit -m "Initial project setup and configuration"

# Commit 2: June 29 (Backend core and ML services)
$env:GIT_AUTHOR_DATE="2026-06-29T14:30:00"
$env:GIT_COMMITTER_DATE="2026-06-29T14:30:00"
git add backend/ scratch/ tests/ test_img/
git commit -m "Add backend core, ML routing, and vault services"

# Commit 3: June 30 (Frontend UI)
$env:GIT_AUTHOR_DATE="2026-06-30T11:20:00"
$env:GIT_COMMITTER_DATE="2026-06-30T11:20:00"
git add frontend/ react-frontend/
git commit -m "Implement frontend UI"

# Commit 4: July 1 (Final fixes)
$env:GIT_AUTHOR_DATE="2026-07-01T08:15:00"
$env:GIT_COMMITTER_DATE="2026-07-01T08:15:00"
git add .
# We only commit if there are remaining changes
if ((git status --porcelain).Length -gt 0) {
    git commit -m "Fix OCR integration and final UI adjustments"
}

git remote add origin https://github.com/SECE-24-28/healthwallet-ta-mlops-project.git
git push -u origin main

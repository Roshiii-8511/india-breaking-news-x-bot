# India Breaking News X Bot

Automation to post daily India news tweets & breaking-news threads on X using GitHub Actions, a News API, and an AI model.

## Project Overview

This project automates the posting of India-focused news updates to X (formerly Twitter) from a personal account. The bot:

- Posts **2–3 short, diplomatic tweets per day** about Indian news developments
- Posts **one in-depth 5-tweet thread each day** explaining the biggest breaking news story
- Uses **GitHub Actions** for automated scheduling
- Fetches news from a **News API** for India headlines
- Generates tweets using an **AI model** (LLM) for writing
- Posts via **X API** to the personal account

### Key Features

- **Diplomatic & neutral tone**: Avoids bias and respects multiple perspectives
- **India-focused**: Exclusive focus on Indian news and breaking developments
- **Safe content**: No hate speech, no extreme bias, no misinformation
- **Character-compliant**: All tweets respect X's 280-character limit
- **Automated**: Runs on a predictable schedule with zero manual intervention
- **Transparent**: No secrets committed to the repo; all API keys stored as GitHub Actions secrets

## Project Phases

### Phase 1: Vision & System Map
**Status: DONE**
- Defined project goals and architecture
- Identified 4 main system components
- Outlined data flow and design principles

### Phase 2: GitHub Repo & Project Skeleton
**Status: IN PROGRESS**
- ✓ Created this repository
- ✓ Set up folder structure (`src/`, `config/`, `docs/`, `.github/workflows/`)
- ✓ Added placeholder files and documentation
- Next: Write core bot logic and configuration

### Phase 3: X Developer App & API Permissions
**Status: PENDING**
- Set up X Developer account
- Create/register X API app
- Generate API keys and access tokens
- Store as GitHub Actions secrets

### Phase 4: News API Setup (India Headlines)
**Status: PENDING**
- Sign up for News API or similar service
- Test API calls for India news
- Generate and store API key as GitHub Actions secret

### Phase 5: AI Provider Setup
**Status: PENDING**
- Choose AI provider (OpenAI, Anthropic, etc.)
- Set up account and API key
- Test prompt engineering for tweet generation
- Store API key as GitHub Actions secret

### Phase 6+: Tweet Logic, Threads & Scheduling
**Status: PENDING**
- Implement news fetching logic
- Build AI-powered tweet generation
- Create tweet scheduling and posting
- Implement safety filters and checks
- Deploy GitHub Actions workflow
- Monitor and iterate

## Security & Secrets

⚠️ **Important**: This repository contains NO secrets, credentials, or API keys.

All sensitive information (API keys, tokens, credentials) are stored as **GitHub Actions secrets** and injected into the environment at runtime.

Secrets that will be added in later phases:
- `X_API_KEY` – X (Twitter) API credentials
- `NEWS_API_KEY` – News API key
- `AI_API_KEY` – AI provider API key

## Project Structure

```
india-breaking-news-x-bot/
├── .github/
│   └── workflows/          # GitHub Actions workflow files (YAML)
├── src/
│   ├── __init__.py
│   └── main.py             # Main bot entry point
├── config/
│   └── CONFIG_NOTES.md     # Configuration documentation
├── docs/
│   └── ARCHITECTURE.md     # High-level system design
├── .gitignore              # Python .gitignore template
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Getting Started (Future Phases)

Once all phases are complete:

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up GitHub Actions secrets for API keys
4. Deploy the workflow to GitHub
5. Monitor the scheduled tweets on X

## Contributing

This is a personal project. Feel free to fork, modify, and adapt for your own use!

## License

MIT License (or your preferred license)

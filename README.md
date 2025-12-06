# India Breaking News X Bot

Automation to post daily India news tweets & breaking-news threads on X using GitHub Actions, a News API, and an AI model.

## Project Overview

This project automates the posting of India-focused news updates to X (formerly Twitter) from a personal account. The bot:

- Posts **2–3 short, diplomatic tweets per day** about Indian news developments
- Posts one **in-depth 5-tweet thread each day** explaining the biggest breaking news story
- Uses **GitHub Actions** for automated scheduling
- Fetches news from a **News API** for India headlines
- Generates tweets using an **AI model** (LLM) for writing
- Posts via **X API** to the personal account

## AI Model

Uses **OpenRouter's free LLM models** (e.g., `meta-llama/llama-3.2-3b-instruct:free`) to generate:
- **5-tweet threads** (one per day) explaining breaking news stories
- **1–2 short diplomatic tweets** (2–3 per day) covering other news developments
- All tweets are **under 280 characters**, maintain a **neutral India-focused tone**, and follow **X platform guidelines**

## Configuration & Secrets

⚠️ **Important**: This repository contains NO secrets, credentials, or API keys.

All sensitive information (API keys, tokens, credentials) are stored as **GitHub Actions secrets** and injected into the environment at runtime.

**Required Secrets:**
- `NEWS_API_KEY` – API key for News API (newsapi.org)
- `OPENROUTER_API_KEY` – API key for OpenRouter (free LLM provider)
- `X_API_KEY` – X (Twitter) API credentials
- `X_API_SECRET` – X API secret
- `X_ACCESS_TOKEN` – X access token
- `X_ACCESS_TOKEN_SECRET` – X access token secret
- `X_BEARER_TOKEN` – X bearer token

## Project Structure

```
india-breaking-news-x-bot/
├── .github/
│   └── workflows/           # GitHub Actions workflow files (YAML)
├── src/
│   ├── __init__.py
│   ├── main.py              # Main bot entry point
│   ├── config.py            # Configuration & environment variables
│   ├── ai_writer.py         # AI tweet generation (OpenRouter integration)
│   ├── news_fetcher.py      # News API integration
│   └── x_poster.py          # X API integration
├── config/
│   └── CONFIG_NOTES.md      # Configuration documentation
├── docs/
│   └── ARCHITECTURE.md      # High-level system design
├── .gitignore               # Python .gitignore template
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Getting Started

### Prerequisites

1. **GitHub Account** – Required for GitHub Actions automation
2. **News API Account** – Sign up at [https://newsapi.org](https://newsapi.org)
3. **OpenRouter Account** – Sign up at [https://openrouter.ai](https://openrouter.ai) for free LLM access
4. **X API Access** – Apply for X API access at [https://developer.twitter.com](https://developer.twitter.com)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/Roshiii-8511/india-breaking-news-x-bot.git
   cd india-breaking-news-x-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up GitHub Actions Secrets**
   - Navigate to your repository settings
   - Go to Secrets and variables → Actions
   - Add the required secrets listed above

4. **Enable GitHub Actions**
   - Ensure the workflow in `.github/workflows/` is enabled
   - Configure the schedule as needed (default: daily posts)

5. **Monitor the scheduled tweets**
   - Check your X account for automated posts
   - Review logs in GitHub Actions for any errors

## Architecture & Components

For a detailed breakdown of system design, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Contributing

This is a personal project. Feel free to fork, modify, and adapt for your own use!

## License

MIT License

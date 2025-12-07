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

Uses **OpenAI's gpt-4o-mini model** to generate:

- **5-tweet threads** (one per day) explaining breaking news stories
- **1–2 short diplomatic tweets** (2–3 per day) covering other news developments
- All tweets are **under 280 characters**, maintain a **neutral India-focused tone**, and follow **X platform guidelines**

## Configuration & Secrets

⚠️**Important**: This repository contains NO secrets, credentials, or API keys.

All sensitive information (API keys, tokens, credentials) are stored as **GitHub Actions secrets** and injected into the environment at runtime.

**Required Secrets:**

- `NEWS_API_KEY` – API key for News API (newsapi.org)
- `OPENAI_API_KEY` – API key for OpenAI API
- `GCP_SERVICE_ACCOUNT_KEY` – GCP service account JSON for Firestore
- `X_CLIENT_ID` – X OAuth2 client ID
- `X_CLIENT_SECRET` – X OAuth2 client secret

**Other X API Credentials** (may be stored as secrets or environment variables):

- `X_API_KEY` – X (Twitter) API key
- `X_API_SECRET` – X API secret
- `X_ACCESS_TOKEN` – X access token
- `X_ACCESS_TOKEN_SECRET` – X access token secret
- `X_BEARER_TOKEN` – X bearer token

## Project Structure

```
india-breaking-news-x-bot/
├── .github/
│   └── workflows/
│       └── auto_tweet.yml              # GitHub Actions workflow (automated scheduling)
├── src/
│   ├── __init__.py
│   ├── main.py                         # Main bot entry point
│   ├── config.py                       # Configuration & environment variables
│   ├── ai_writer.py                    # AI tweet generation (OpenAI integration)
│   ├── news_fetcher.py                 # News API integration
│   ├── x_poster.py                     # X API integration
│   └── token_refresh.py                # X OAuth2 token refresh
├── config/
│   └── CONFIG_NOTES.md                 # Configuration documentation
├── docs/
│   └── ARCHITECTURE.md                 # High-level system design
├── .gitignore
├── requirements.txt                    # Python dependencies
└── README.md                           # This file
```

## Getting Started

### Prerequisites

1. **GitHub Account** – Required for GitHub Actions automation
2. **News API Account** – Sign up at https://newsapi.org
3. **OpenAI Account** – Sign up at https://platform.openai.com for API access
4. **X API Access** – Apply for X API access at https://developer.twitter.com
5. **Google Cloud Account** – For Firestore OAuth2 token storage

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
   - Ensure the workflow in `.github/workflows/auto_tweet.yml` is enabled
   - Configure the schedule as needed (default: daily posts)

5. **Initialize Firestore**
   - Create a Firestore collection `x_tokens` with document `personal_bot`
   - Add your X OAuth2 refresh token to this document
   - See `config/CONFIG_NOTES.md` for detailed instructions

6. **Monitor the scheduled tweets**
   - Check your X account for automated posts
   - Review logs in GitHub Actions for any errors

## Architecture & Components

For a detailed breakdown of system design, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Key Features

- **Automated Scheduling**: Posts tweets on a schedule using GitHub Actions
- **News Integration**: Fetches latest India news from News API
- **AI-Powered Writing**: Uses OpenAI's gpt-4o-mini for intelligent tweet generation
- **OAuth2 Token Refresh**: Automatically rotates X OAuth2 tokens stored in Firestore
- **Multi-Tweet Threads**: Posts coherent 5-tweet threads explaining breaking news
- **Diplomatic Tone**: Maintains a neutral, professional tone suitable for news coverage

## Contributing

This is a personal project. Feel free to fork, modify, and adapt for your own use!

## License

MIT License

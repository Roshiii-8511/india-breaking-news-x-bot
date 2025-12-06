# System Architecture: India Breaking News X Bot

## Overview

This document describes the high-level architecture and design of the India Breaking News X Bot—an automated system that posts daily news tweets and breaking-news threads to X (formerly Twitter) from a personal account.

## 4 Main System Components

### 1. Scheduler (GitHub Actions)
- Triggers the entire bot 2–3 times per day using cron schedules.
- Manages execution timing and workflow orchestration.
- Runs the Python script automatically without manual intervention.

### 2. News Collector (News API)
- Fetches the latest India news headlines from a News API service.
- Filters and prioritizes stories by recency and relevance.
- Identifies the single biggest breaking story and a selection of smaller stories.

### 3. AI Writer (LLM)
- Receives news summaries from the News Collector.
- Generates short, diplomatic tweets for smaller stories (under 280 characters each).
- Creates a detailed 5-tweet thread explaining the breaking news story.
- Ensures neutral, balanced language that respects multiple perspectives.

### 4. X Poster (X API)
- Uses X API credentials to authenticate as the personal account.
- Posts individual tweets for smaller news stories.
- Tweets the breaking news as a threaded sequence (5 connected tweets).
- Handles API rate limiting and error recovery.

## Data Flow

1. GitHub Actions triggers the scheduled job at the configured time.
2. The bot script queries the News API for latest India headlines.
3. The script selects the top breaking story and a few secondary stories.
4. The AI model receives story summaries and generates tweets:
   - Short diplomatic tweets for secondary stories.
   - A detailed 5-tweet thread for the breaking news explainer.
5. The X Poster receives tweet text and posts them via the X API:
   - Posts normal tweets for smaller stories.
   - Posts tweets as a thread (reply chain) for the breaking news.
6. Logs are recorded for monitoring and debugging.

## Design Principles

- **Diplomatic & Neutral Tone**: All tweets avoid bias and extreme viewpoints.
- **India-Focused Content**: Exclusive focus on Indian news and breaking developments.
- **No Hate Speech**: System prevents hateful or discriminatory language.
- **Character Limit Compliance**: Every tweet respects X's 280-character limit.
- **Rumour Avoidance**: System avoids spreading unverified rumors or misinformation.
- **Automated & Scheduled**: Runs autonomously on a predictable schedule.

## Security & Secrets

- API keys and tokens (News API key, X API credentials) are stored as GitHub Actions secrets.
- No secrets are committed to the repository.
- Secrets are injected into the environment at runtime.

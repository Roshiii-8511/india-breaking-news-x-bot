# Configuration Notes

## Environment Variables & GitHub Secrets

This project requires the following environment variables to be set as GitHub Secrets. **None of these values should be committed to the repository.**

### Required Secrets

#### 1. `NEWS_API_KEY`
- **Description**: API key for News API (newsapi.org)
- **How to get**: Sign up at https://newsapi.org and generate an API key
- **Usage**: Fetches India news headlines for the bot to post

#### 2. `OPENROUTER_API_KEY`
- **Description**: API key for OpenRouter (free LLM provider)
- **How to get**: Sign up at https://openrouter.ai and generate an API key
- **Usage**: Generates tweet content using free-tier models (meta-llama/llama-3.2-3b-instruct:free)
- **Cost**: Free tier provides ~50 requests/day, sufficient for 2-3 runs/day (1-2 requests per run for tweet generation)
- **Note**: No credit card required; completely free

#### 3. `GCP_SERVICE_ACCOUNT_KEY`
- **Description**: Full JSON credentials for a Google Cloud service account with Firestore access
- **How to get**:
  1. Create a GCP project
  2. Enable Firestore API
  3. Create a Service Account with Firestore permissions
  4. Generate a JSON key
  5. Copy the entire JSON content and paste as secret value
- **Usage**: Stores and rotates X OAuth2 refresh tokens in Firestore

#### 4. `X_CLIENT_ID`
- **Description**: X (Twitter) OAuth2 client ID for the bot application
- **How to get**:
  1. Go to https://developer.twitter.com/en/portal/dashboard
  2. Create an app or use existing one
  3. Set up OAuth2 authentication
  4. Copy the Client ID from OAuth2 settings
- **Usage**: Used in X OAuth2 token refresh flow

### Optional Secrets

- `DEBUG_MODE`: Set to `true` to enable verbose logging (default: `false`)

## Firestore Setup

### Initial Token Storage

Before running the bot, you must manually initialize the refresh token in Firestore:

1. Go to Google Cloud Firestore console
2. Create collection: `x_tokens`
3. Create document: `personal_bot` in that collection
4. Add field: `refresh_token` with your X OAuth2 refresh token value
5. Optionally add field: `updated_at` with current timestamp

After the first successful run, the refresh token will be automatically rotated and updated.

## GitHub Actions Configuration

The workflow file `.github/workflows/auto_tweet.yml` runs the bot on schedule:
- **09:15 IST** (~03:45 UTC)
- **15:15 IST** (~09:45 UTC)
- **21:15 IST** (~15:45 UTC)

Adjust cron times in the workflow file as needed.

## OpenRouter Free-Tier Model

**Model Used**: `meta-llama/llama-3.2-3b-instruct:free`

- **Why Free-Tier**: Completely free with no credit card required
- **Requests/Day**: ~50 free requests per day
- **Per Run Cost**: ~1-2 requests (thread + short tweets)
- **Quality**: Llama 3.2 3B is suitable for news tweet generation with proper prompting
- **Alternative Models**: You can change the model in `src/config.py` by setting `OPENROUTER_MODEL` to any OpenRouter :free model

## API Rate Limits

- **News API**: Free tier has 100 requests/day
- **OpenRouter**: Free tier has ~50 requests/day (sufficient for 2-3 runs/day)
- **X API**: v2 API limits apply; check Twitter Developer documentation
- **Firestore**: Free tier supports 50k reads/day

## Troubleshooting

If the bot fails:
1. Check GitHub Actions logs in the repo
2. Verify all secrets are set correctly
3. Check Firestore document exists with refresh_token field
4. Ensure X OAuth2 client has proper permissions
5. Verify News API key is active
6. Verify OpenRouter API key is active and has free-tier access

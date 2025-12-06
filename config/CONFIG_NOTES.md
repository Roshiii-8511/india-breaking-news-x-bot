# Configuration Notes

## Environment Variables & GitHub Secrets

This project requires the following environment variables to be set as GitHub Secrets. **None of these values should be committed to the repository.**

### Required Secrets

#### 1. `NEWS_API_KEY`
- **Description**: API key for News API (newsapi.org)
- **How to get**: Sign up at https://newsapi.org and generate an API key
- **Usage**: Fetches India news headlines for the bot to post

#### 2. `OPENAI_API_KEY`
- **Description**: API key for OpenAI (for GPT models)
- **How to get**: Create account at https://openai.com/api and generate an API key
- **Usage**: Generates tweet content using AI models (gpt-4o-mini or gpt-4-turbo)

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

## API Rate Limits

- **News API**: Free tier has 100 requests/day
- **OpenAI**: Rates depend on your API plan
- **X API**: v2 API limits apply; check Twitter Developer documentation
- **Firestore**: Free tier supports 50k reads/day

## Troubleshooting

If the bot fails:
1. Check GitHub Actions logs in the repo
2. Verify all secrets are set correctly
3. Check Firestore document exists with refresh_token field
4. Ensure X OAuth2 client has proper permissions
5. Verify News API and OpenAI keys are active

# Configuration Notes

## Environment Variables & GitHub Secrets

This project requires the following environment variables to be set as GitHub Secrets. **None of these values should be committed to the repository.**

### Required Secrets

#### 1. `NEWS_API_KEY`

- **Description**: API key for News API (newsapi.org)
- **How to get**: Sign up at https://newsapi.org and generate an API key
- **Usage**: Fetches India news headlines for the bot to post

#### 2. `OPENAI_API_KEY`

- **Description**: API key for OpenAI API
- **How to get**: Sign up at https://platform.openai.com and create an API key in your account settings
- **Usage**: Generates tweet content using OpenAI's gpt-4o-mini model
- **Cost**: Free tier provides $5 in API credits; typical usage costs minimal amounts
- **Note**: Credit card required for sign-up, but charges only apply after credits are exhausted

#### 3. `GCP_SERVICE_ACCOUNT_KEY`

- **Description**: Full JSON credentials for a Google Cloud service account with Firestore access
- **How to get**:
  - Create a GCP project
  - Enable Firestore API
  - Create a Service Account with Firestore permissions
  - Generate a JSON key
  - Copy the entire JSON content and paste as secret value
- **Usage**: Stores and rotates X OAuth2 refresh tokens in Firestore

#### 4. `X_CLIENT_ID`

- **Description**: X (Twitter) OAuth2 client ID for the bot application
- **How to get**:
  - Go to https://developer.twitter.com/en/portal/dashboard
  - Create an app or use existing one
  - Set up OAuth2 authentication
  - Copy the Client ID from OAuth2 settings
- **Usage**: Used in X OAuth2 token refresh flow

#### 5. `X_CLIENT_SECRET`

- **Description**: X (Twitter) OAuth2 client secret for the bot application
- **How to get**:
  - Go to https://developer.twitter.com/en/portal/dashboard
  - Navigate to your app's OAuth2 settings
  - Copy the Client Secret
- **Usage**: Used in X OAuth2 token refresh flow with basic auth header

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

## OpenAI Model Configuration

**Model Used**: `gpt-4o-mini`

- **Why gpt-4o-mini**: Cost-effective, fast, and suitable for tweet generation tasks
- **Free Tier**: $5 in initial API credits
- **Per Run Cost**: Minimal (typically <$0.01 per run for tweet generation)
- **Quality**: GPT-4o mini provides excellent quality for news tweet generation
- **Rate Limits**: Check OpenAI documentation for current rate limits; generous for low-volume usage
- **Alternative Models**: You can change the model in `src/config.py` by setting `OPENAI_MODEL` to any available OpenAI model (gpt-4, gpt-4-turbo, gpt-3.5-turbo, etc.)

## API Rate Limits

- **News API**: Free tier has 100 requests/day
- **OpenAI**: Token-based billing; free tier has $5 in credits
- **X API**: v2 API limits apply; check Twitter Developer documentation
- **Firestore**: Free tier supports 50k reads/day

## Troubleshooting

If the bot fails:

1. Check GitHub Actions logs in the repo
2. Verify all secrets are set correctly
3. Check Firestore document exists with refresh_token field
4. Ensure X OAuth2 client has proper permissions
5. Verify News API key is active
6. Verify OpenAI API key is active and has remaining credits

# Quick Start Guide

## CLI Version (Fastest Setup)

1. **Install dependencies**
   ```bash
   pipenv install
   pipenv shell
   ```

2. **Run the CLI**
   ```bash
   python cli/mastodon_quotability_cli.py --instance YOUR_INSTANCE.social info
   ```

3. **Enable quotability**
   ```bash
   python cli/mastodon_quotability_cli.py --instance YOUR_INSTANCE.social enable --policy public
   ```

Replace `YOUR_INSTANCE.social` with your actual Mastodon instance (e.g., `mastodon.social`, `fosstodon.org`, etc.)

## Web App Version (Full UI Experience)

1. **Install Python dependencies**
   ```bash
   pipenv install
   ```

2. **Install Node dependencies**
   ```bash
   cd webapp/frontend
   npm install
   cd ../..
   ```

3. **Start the backend** (Terminal 1)
   ```bash
   pipenv shell
   python webapp/backend/app.py
   ```

4. **Start the frontend** (Terminal 2)
   ```bash
   cd webapp/frontend
   npm run dev
   ```

5. **Open browser**
   - Navigate to http://localhost:5173
   - Enter your Mastodon instance URL
   - Follow the OAuth flow
   - Enable quotability!

## First Time Setup

When you first run the app (CLI or web), you'll need to:

1. **Authorize the application**: A browser window will open asking you to authorize "Mastodon Quotability Manager"
2. **Copy the authorization code**: After authorizing, you'll receive a code
3. **Paste the code**: Enter it in the CLI or web interface
4. **Done!**: Your credentials are saved locally for future use

## What This Tool Does

- Connects to your Mastodon server via OAuth
- Fetches all your posts
- Updates each post to allow quoting (using Mastodon 4.5+ API)
- Shows progress and results

## Important Notes

- ✅ This only works with Mastodon 4.5+ servers
- ✅ This is a ONE-TIME operation (you don't need to run it again)
- ✅ Private and direct messages are skipped automatically
- ✅ Your credentials are stored locally and securely
- ⚠️ This may take a while if you have many posts (rate limiting applies)

## Troubleshooting

**"Module not found" error?**
```bash
pipenv install
pipenv shell
```

**Backend won't start?**
- Make sure port 5000 is not in use
- Check that Pipenv dependencies are installed

**Frontend won't start?**
- Make sure you're in `webapp/frontend` directory
- Run `npm install` first
- Check that port 5173 is not in use

**OAuth errors?**
- Make sure your instance URL is correct
- Try with and without `https://` prefix
- Some instances may not be running Mastodon 4.5+ yet

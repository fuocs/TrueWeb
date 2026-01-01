# TrueWeb-GUI - Environment Setup

## Setting up API Keys

To protect sensitive API keys from being leaked to GitHub, this project uses environment variables stored in a `.env` file.

### Setup Instructions:

1. **Copy the example file:**
   ```bash
   cd backend
   cp .env.example .env
   ```

2. **Edit `.env` file and add your API keys:**
   - `SERVICE_ACCOUNT_CONFIG`: Your Firebase service account JSON (as single-line string)
   - `GOOGLE_CLIENT_CONFIG`: Your Google OAuth client config JSON (as single-line string)
   - `FIREBASE_WEB_API_KEY`: Your Firebase Web API key
   - `VIRUSTOTAL_API_KEY`: Get from [VirusTotal](https://www.virustotal.com/gui/my-apikey)
   - `GOOGLE_SAFE_BROWSING_API_KEY`: Get from [Google Cloud Console](https://console.cloud.google.com/)

3. **Important:** 
   - The `.env` file is already in `.gitignore` and will NOT be committed to GitHub
   - Never share your `.env` file or commit it to version control
   - Always use `.env.example` as a template for other developers

### For PyInstaller builds:

The application will automatically load environment variables from the `.env` file using `python-dotenv`. Make sure this package is installed:

```bash
pip install python-dotenv
```

Or if using uv:
```bash
uv pip install python-dotenv
```

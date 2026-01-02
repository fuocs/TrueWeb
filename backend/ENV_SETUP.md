# TrueWeb - Environment Setup

## Setting up API Keys

To protect sensitive API keys from being leaked to GitHub, this project uses environment variables stored in a `.env` file.

### Setup Instructions:

1. **Copy the example file:**
   ```bash
   cd backend
   cp .env.example .env
   ```

2. **Edit `.env` file and add your API keys:**

   | Variable | Description | Where to get |
   |----------|-------------|--------------|
   | `SERVICE_ACCOUNT_CONFIG` | Firebase Admin SDK JSON (single-line) | Firebase Console → Project Settings → Service Accounts |
   | `GOOGLE_CLIENT_CONFIG` | Google OAuth client config JSON | Google Cloud Console → Credentials |
   | `FIREBASE_WEB_API_KEY` | Firebase Web API key | Firebase Console → Project Settings → General |
   | `VIRUSTOTAL_API_KEY` | VirusTotal API key | [VirusTotal API](https://www.virustotal.com/gui/my-apikey) |
   | `GOOGLE_SAFE_BROWSING_API_KEY` | Google Safe Browsing API | [Google Cloud Console](https://console.cloud.google.com/) |
   | `GROQ_API_KEY` | Groq AI API key(s) | [Groq Console](https://console.groq.com/keys) |

3. **Multiple Groq API Keys (Recommended):**
   
   To avoid rate limits, you can provide multiple Groq API keys separated by commas:
   ```env
   GROQ_API_KEY='key1,key2,key3,key4,key5'
   ```
   The application will automatically rotate through keys when rate limits are hit.

4. **Important Security Notes:** 
   - The `.env` file is in `.gitignore` and will NOT be committed to GitHub
   - Never share your `.env` file or commit it to version control
   - Always use `.env.example` as a template for other developers
   - Keep `serviceAccountKey.json` private (also gitignored)

### For PyInstaller Builds:

When running the built `.exe` file:
1. Place the `.env` file in the **same directory** as the executable
2. The application will automatically detect and load it
3. You can modify API keys without rebuilding the application

```bash
dist/
└── TrueWeb/
    ├── TrueWeb.exe
    └── .env          ← Place your .env file here
```

### Verifying Setup:

Run this command to test if environment variables are loaded correctly:
```bash
python backend/env_loader.py
```

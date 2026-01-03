# TrueWeb - Environment Setup

## Setting up API Keys

To protect sensitive API keys from being leaked to GitHub, this project uses environment variables stored in a `.env` file.

### ⚠️ IMPORTANT: File Location

**The `.env` file MUST be created in the `backend/` directory, NOT in the root folder.**

```
TrueWeb-GUI/
├── backend/
│   └── .env          ← CREATE YOUR .env FILE HERE
├── .env.example      ← Template file (in root)
└── ENV_SETUP.md      ← This file
```

### Setup Instructions:

1. **Copy the example file to the backend directory:**
   ```bash
   # From project root
   cp .env.example backend/.env
   
   # Or manually create backend/.env and copy content from .env.example
   ```

2. **Edit `backend/.env` file and add your API keys:**

   | Variable | Description | Where to get |
   |----------|-------------|--------------|
   | `SERVICE_ACCOUNT_CONFIG` | Firebase Admin SDK JSON (single-line) | Firebase Console → Project Settings → Service Accounts |
   | `GOOGLE_CLIENT_CONFIG` | Google OAuth client config JSON | Google Cloud Console → Credentials |
   | `FIREBASE_WEB_API_KEY` | Firebase Web API key | Firebase Console → Project Settings → General |
   | `VIRUSTOTAL_API_KEY` | VirusTotal API key (PRIMARY) | [VirusTotal API](https://www.virustotal.com/gui/my-apikey) |
   | `GOOGLE_SAFE_BROWSING_API_KEY` | Google Safe Browsing API (OPTIONAL) | [Google Cloud Console](https://console.cloud.google.com/apis/library/safebrowsing.googleapis.com) |
   | `GROQ_API_KEY` | Groq AI API key(s) | [Groq Console](https://console.groq.com/keys) |

3. **Multiple Groq API Keys (Recommended):**
   
   To avoid rate limits, you can provide multiple Groq API keys separated by commas:
   ```env
   GROQ_API_KEY='key1,key2,key3,key4,key5,key6,key7,key8,key9,key10'
   ```
   The application will automatically rotate through keys when rate limits are hit. **More keys = fewer rate limits!**

4. **Google Safe Browsing Setup (OPTIONAL):**
   
   This is a secondary reputation check. If you skip this, TrueWeb will still work using VirusTotal.
   
   Steps to get API key:
   1. Visit: https://console.cloud.google.com/apis/library/safebrowsing.googleapis.com
   2. Select your Google Cloud project (or create a new one)
   3. Click **"Enable"** button
   4. Set up OAuth consent screen (if first time)
   5. Go to **"Credentials"** → **"+ CREATE CREDENTIALS"** → **"API key"**
   6. Copy your API key

5. **Important Security Notes:** 
   - The `backend/.env` file is in `.gitignore` and will NOT be committed to GitHub
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
    └── .env          ← Place your .env file here (for standalone builds)
```

### Verifying Setup:

Run this command to test if environment variables are loaded correctly:
```bash
python backend/env_loader.py
```

If successful, you should see all your API keys loaded (values will be masked for security).

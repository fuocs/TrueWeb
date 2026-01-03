# TrueWeb 🛡️

**Advanced Website Security Analysis Tool** - A comprehensive desktop application with browser extension for real-time website safety assessment.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.10%2B-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)

## 🌟 Features

- **🤖 AI-Powered Analysis**: Utilizes Groq AI for intelligent content evaluation with 10-key load balancing
- **🔍 Multi-Layer Security Checks**:
  - VirusTotal integration for malware detection
  - Google Safe Browsing API
  - SSL/TLS certificate validation
  - Domain age and reputation analysis
  - HTML heuristic pattern detection
  - Whois information lookup
- **📊 Smart Scoring System**: Weighted scoring algorithm with configurable thresholds
- **🌐 Browser Extension**: Real-time website checking via Chrome/Edge extension
- **💾 Firebase Integration**: User authentication and review system
- **🖥️ System Tray**: Background operation with quick access
- **📱 Modern UI**: Clean PyQt6 interface with responsive design

## 🏗️ Architecture

```
TrueWeb-GUI/
├── main.py                 # Main application entry point
├── app.py                  # Application controller
├── backend/                # Core analysis modules
│   ├── scoring_system.py   # Orchestrates security checks
│   ├── reputation.py       # VirusTotal & Safe Browsing
│   ├── AI_confidence.py    # Groq AI analysis
│   ├── ssl_certificate.py  # SSL validation
│   ├── html_heuristic.py   # Pattern detection
│   ├── firebaseDB.py       # Database operations
│   ├── localserver.py      # Flask server for extension
│   └── services/           # Supporting services
├── frontend/               # PyQt6 UI components
│   ├── main_window.py      # Primary window
│   ├── result_page.py      # Analysis results display
│   ├── loading_page.py     # Progress indicator
│   └── media/              # UI assets
└── extension/              # Browser extension
    ├── manifest.json       # Extension configuration
    ├── background.js       # Background service worker
    └── content.js          # Content script
```

## 📋 Prerequisites

- **Python**: 3.10 or higher
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 20.04+)
- **API Keys** (required):
  - Groq API keys (multiple keys = fewer rate limits)
  - VirusTotal API key
  - Google Safe Browsing API key
  - Firebase credentials

## 🚀 Installation

### Option 1: Using `uv` (Recommended - Fast & Cross-Platform)

[`uv`](https://docs.astral.sh/uv/) is an extremely fast Python package and project manager, written in Rust. It's 10-100x faster than `pip` and replaces `pip`, `pip-tools`, `pipx`, `poetry`, `pyenv`, `virtualenv`, and more.

#### 1. Install uv

**Standalone Installers (Recommended):**

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Or install via PyPI:**
```bash
# With pip
pip install uv

# Or pipx (isolated installation)
pipx install uv
```

**Update uv (if installed via standalone installer):**
```bash
uv self update
```

📖 **Full installation guide:** https://docs.astral.sh/uv/getting-started/installation/

#### 2. Clone and Setup
```bash
git clone https://github.com/fuocs/TrueWeb.git
cd TrueWeb
```

#### 3. Install Dependencies & Run
```bash
# Create virtual environment and install all dependencies (automatic)
uv sync

# Run the application
uv run python main.py
```

That's it! `uv` automatically handles Python version management, virtual environment creation, and dependency installation.

**Alternative commands:**
```bash
# Run directly without activating venv
uv run python main.py

# Or activate venv first, then run normally
# Windows:
.venv\Scripts\activate
python main.py

# macOS/Linux:
source .venv/bin/activate
python main.py
```

### Option 2: Using pip (Traditional)

#### 1. Clone the Repository
```bash
git clone https://github.com/fuocs/TrueWeb.git
cd TrueWeb
```

#### 2. Create Virtual Environment
**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Run the Application
```bash
python main.py
```

### Configure Environment Variables (Required for both methods)

**⚠️ IMPORTANT:** The `.env` file must be created in the `backend/` directory.

```bash
# From project root, copy template to backend/
cp .env.example backend/.env

# Then edit backend/.env with your API keys
```

For detailed setup instructions, see [ENV_SETUP.md](ENV_SETUP.md)

Quick reference - Edit `backend/.env` and add your API keys:

```env
# Firebase Admin SDK (for Database & User Creation)
SERVICE_ACCOUNT_CONFIG='{"type":"service_account","project_id":"your_project",...}'

# Google OAuth Client Config
GOOGLE_CLIENT_CONFIG='{"web":{"client_id":"...","client_secret":"..."}}'

# Firebase Web API Key (for Login/Authentication)
FIREBASE_WEB_API_KEY=your_firebase_web_api_key

# VirusTotal API Key (PRIMARY - Required)
VIRUSTOTAL_API_KEY=your_virustotal_api_key

# Google Safe Browsing API Key (OPTIONAL - Secondary check)
GOOGLE_SAFE_BROWSING_API_KEY=your_gsb_api_key

# Groq AI API Keys (comma-separated for load balancing)
GROQ_API_KEY=key1,key2,key3,key4,key5,key6,key7,key8,key9,key10
```

**📌 Getting API Keys:**

#### Required APIs:
- **Groq AI** (Primary): Sign up at https://console.groq.com/keys
- **VirusTotal** (PRIMARY reputation check): https://www.virustotal.com/gui/my-apikey
- **Firebase**: Create project at https://console.firebase.google.com

#### Optional APIs:
- **Google Safe Browsing** (OPTIONAL - Secondary reputation check):
  1. Visit: https://console.cloud.google.com/apis/library/safebrowsing.googleapis.com?project=gen-lang-client-0432606952
  2. Click **"Enable"** button to activate the API
  3. **Set up OAuth consent screen** (if first time):
     - Go to "OAuth consent screen" in left menu
     - Choose "External" user type
     - Fill in required fields (app name, email)
  4. Click **"Credentials"** in left menu
  5. Click **"+ CREATE CREDENTIALS"** button at top
  6. Select **"API key"** from dropdown
  7. Copy your new API key
  
  **Note**: Google Safe Browsing is a secondary check. If you skip this, TrueWeb will still work using VirusTotal as the primary reputation database.

**Firebase Setup Note**: For `SERVICE_ACCOUNT_CONFIG`, download the JSON from Firebase Console → Project Settings → Service Accounts → Generate new private key, then paste as a single-line string.

#### 5. Run the Application
```bash
python main.py
```

### Option 2: Build Standalone Executable

#### Build with PyInstaller

**Windows:**
```powershell
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller TrueWeb.spec
```

The executable will be created in `dist/TrueWeb/`:
- `TrueWeb.exe` (main executable)
- Copy your `.env` file to the same directory as the .exe
- Run `TrueWeb.exe`

**macOS:**
```bash
pyinstaller TrueWeb.spec
# Output: dist/TrueWeb.app
```

**Linux:**
```bash
pyinstaller TrueWeb.spec
# Output: dist/TrueWeb/TrueWeb
```

**⚠️ Important**: When running the .exe, place the `.env` file in the same directory as the executable. The application will automatically detect and load it.

## 🌐 Browser Extension Setup

### Chrome/Edge Installation

1. Open Chrome/Edge and navigate to `chrome://extensions/` or `edge://extensions/`
2. Enable **Developer mode** (toggle in top-right)
3. Click **Load unpacked**
4. Select the `extension/` folder from this repository
5. The TrueWeb icon should appear in your toolbar

### Usage

1. Start the TrueWeb desktop application (it runs a local server on port 38999)
2. Click the TrueWeb extension icon while on any website
3. The extension sends the URL to the desktop app for analysis
4. Results appear in the desktop application

## 📖 Usage Guide

### Desktop Application

1. **Login**: Sign in with Google account (requires Firebase authentication)
2. **Search**: Enter a URL in the search box or use the browser extension
3. **Analysis**: Wait while TrueWeb performs multi-layer security checks:
   - 🌐 Connectivity check
   - 🤖 AI content analysis
   - 🔍 Reputation database lookup
   - 🔒 SSL certificate validation
   - 📊 Domain age verification
   - 🕵️ Pattern analysis
4. **Results**: View comprehensive safety score and detailed breakdown
5. **Review**: Submit or read community reviews

### Scoring System

- **Score < 3.0**: ⚠️ **POTENTIALLY UNSAFE** - Avoid visiting
- **Score 3.0 - 4.0**: ⚡ **USE WITH CAUTION** - Verify carefully
- **Score > 4.0**: ✅ **CAN BE TRUSTED** - Generally safe

Scores are weighted based on:
- Reputation Database: 2.0x
- AI Analysis: 1.5x
- Domain Age: 1.0x
- SSL Certificate: 1.2x
- HTML Heuristics: 0.8x

## 🔧 Configuration

### Customizing Thresholds

Edit `backend/config.py`:

```python
SCORE_WEIGHTS = {
    'Reputation Databases': 2.0,
    'AI analysis': 1.5,
    'Domain age': 1.0,
    'SSL certificate': 1.2,
    'HTML heuristics': 0.8,
}

THRESHOLDS = {
    'unsafe': 3.0,
    'caution': 4.0,
}
```

## 🐛 Troubleshooting

### "Connection Failed" Error

If websites like `portal.hcmus.edu.vn` fail to connect:
- The app automatically handles SSL verification bypass for self-signed certificates
- Check your internet connection
- Verify the URL is correct and accessible

### "Rate Limit Exceeded" for AI Analysis

- Ensure you have multiple Groq API keys configured (comma-separated in `.env`)
- The app automatically rotates through keys when rate limits are hit
- Consider upgrading your Groq plan

### Extension Not Connecting

- Ensure the desktop app is running (check system tray)
- Verify local server is on port 38999: `netstat -ano | findstr 38999`
- Check extension permissions in `chrome://extensions`

### PyInstaller Build Issues

**Windows Defender blocking .exe:**
```powershell
# Add exclusion
Add-MpPreference -ExclusionPath "C:\path\to\dist\TrueWeb"
```

**Missing .env file:**
- Always copy `.env` to the same directory as the .exe
- Check logs in the console for environment loading messages

## 🧪 Testing

Run quick tests to verify setup:

```bash
# Test environment loading
python backend/env_loader.py

# Test Groq API connection
python -c "from backend.AI_confidence import check_groq_keys; check_groq_keys()"

# Test scoring system
python backend/scoring_system.py --test
```

## 📦 Dependencies

Key libraries (see `pyproject.toml` for full list):

- **PyQt6** (>=6.10.0): GUI framework
- **Flask** (>=3.1.2): Local server for extension
- **requests** (>=2.32.5): HTTP client
- **python-dotenv** (>=1.2.1): Environment management
- **beautifulsoup4**: HTML parsing
- **Pillow**: Image processing
- **firebase-admin**: Firebase integration
- **groq**: AI analysis API

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the **MIT License** - see below for details.

```
MIT License

Copyright (c) 2026 TrueWeb Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- **Groq** for providing fast AI inference
- **VirusTotal** for malware detection API
- **Google Safe Browsing** for threat intelligence
- **PyQt6** for the excellent GUI framework
- **Firebase** for backend services

## 📞 Support

- **Issues**: Report bugs on [GitHub Issues](https://github.com/fuocs/TrueWeb/issues)
- **Documentation**: See [ENV_SETUP.md](backend/ENV_SETUP.md) for detailed environment setup

## 🔒 Security Notice

This tool is designed for educational and security research purposes. Always:
- Keep your API keys confidential (never commit `.env` to git)
- Use HTTPS for production deployments
- Review the code before running on sensitive systems
- Update dependencies regularly for security patches

---

**Made with ❤️ for a safer web**

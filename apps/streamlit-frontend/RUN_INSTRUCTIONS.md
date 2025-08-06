# Running the RPM Streamlit Application Locally

## Quick Start

### 🍎 Mac/Linux Users
```bash
./run_local.sh
```
Or:
```bash
python3 run_local.py
```

### 🪟 Windows Users
Double-click `run_local.bat`

Or from Command Prompt/PowerShell:
```cmd
python run_local.py
```

## What the Script Does

The `run_local.py` script will:

1. ✅ Check Python version (requires 3.8+)
2. ✅ Check if Streamlit is installed
3. 📦 Install requirements if needed
4. ⚠️ Check if backend is running (warning only)
5. 🚀 Start the Streamlit app at http://localhost:8501

## Prerequisites

### Required
- Python 3.8 or higher
- Internet connection (for installing packages)

### Recommended
- Backend API running at http://localhost:8000
  ```bash
  cd ../backend
  python main.py
  ```

## Manual Installation (if script fails)

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Run Streamlit:
   ```bash
   streamlit run app.py
   ```

## Troubleshooting

### Python not found
- **Mac**: Install from https://python.org or use `brew install python3`
- **Windows**: Install from https://python.org and add to PATH

### Permission denied (Mac/Linux)
```bash
chmod +x run_local.sh
```

### Module not found errors
```bash
pip install -r requirements.txt
```

### Backend connection error
Make sure the backend is running:
```bash
cd ../backend
python main.py
```

## Configuration

The app will run with:
- **URL**: http://localhost:8501
- **Theme**: Dark mode with green accent
- **Backend**: Expected at http://localhost:8000

## Default Credentials

When the app starts, use these test credentials:
- **Username**: testuser
- **Password**: testpass

## Features Available Locally

✅ Portfolio Overview
✅ Site Analysis with Power Curves
✅ Skid Performance Monitoring
✅ Real-time Data from Backend
✅ Dark Theme UI

## Stopping the Application

Press `Ctrl+C` in the terminal to stop the Streamlit server.

---

For more help, see the main project README or open an issue on GitHub.
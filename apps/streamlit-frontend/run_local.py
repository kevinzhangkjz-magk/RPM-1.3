#!/usr/bin/env python3
"""
Cross-platform script to run the RPM Streamlit application locally
Works on both Windows and Mac/Linux
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# Colors for terminal output (works on both Windows and Unix)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.GREEN):
    """Print colored message to terminal"""
    print(f"{color}{message}{Colors.ENDC}")

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_colored(f"❌ Python 3.8+ required. You have {version.major}.{version.minor}", Colors.RED)
        sys.exit(1)
    print_colored(f"✅ Python {version.major}.{version.minor} detected", Colors.GREEN)

def check_streamlit_installed():
    """Check if Streamlit is installed"""
    try:
        import streamlit
        version = streamlit.__version__
        print_colored(f"✅ Streamlit {version} is installed", Colors.GREEN)
        return True
    except ImportError:
        print_colored("❌ Streamlit is not installed", Colors.RED)
        return False

def install_requirements():
    """Install requirements if needed"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print_colored("⚠️  requirements.txt not found", Colors.YELLOW)
        return False
    
    print_colored("📦 Installing requirements...", Colors.BLUE)
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "--quiet"
        ])
        print_colored("✅ Requirements installed successfully", Colors.GREEN)
        return True
    except subprocess.CalledProcessError:
        print_colored("❌ Failed to install requirements", Colors.RED)
        return False

def check_backend_running():
    """Check if backend is running and accessible"""
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print_colored("✅ Backend is running at http://localhost:8000", Colors.GREEN)
            return True
    except:
        pass
    
    print_colored("⚠️  Backend not detected at http://localhost:8000", Colors.YELLOW)
    print_colored("   Make sure to start the backend server first:", Colors.YELLOW)
    print_colored("   cd ../backend && python main.py", Colors.YELLOW)
    return False

def run_streamlit():
    """Run the Streamlit application"""
    app_file = Path(__file__).parent / "app.py"
    
    if not app_file.exists():
        print_colored(f"❌ app.py not found at {app_file}", Colors.RED)
        sys.exit(1)
    
    # Set environment variables
    os.environ["STREAMLIT_SERVER_PORT"] = "8501"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "localhost"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    
    # Streamlit configuration
    config_options = [
        "--server.port=8501",
        "--server.address=localhost",
        "--browser.gatherUsageStats=false",
        "--theme.base=dark",
        "--theme.primaryColor=#54b892",
        "--theme.backgroundColor=#1b2437",
        "--theme.secondaryBackgroundColor=#2d3748",
        "--theme.textColor=#f0f0f0"
    ]
    
    print_colored("\n" + "="*60, Colors.BOLD)
    print_colored("🚀 Starting RPM Streamlit Application", Colors.HEADER)
    print_colored("="*60, Colors.BOLD)
    print_colored(f"📍 URL: http://localhost:8501", Colors.BLUE)
    print_colored(f"📁 Working Directory: {Path.cwd()}", Colors.BLUE)
    print_colored(f"🖥️  Platform: {platform.system()} {platform.release()}", Colors.BLUE)
    print_colored("="*60 + "\n", Colors.BOLD)
    
    # Build the command
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_file)] + config_options
    
    try:
        # Run Streamlit
        if platform.system() == "Windows":
            # Windows-specific handling
            subprocess.run(cmd, shell=False)
        else:
            # Mac/Linux handling
            subprocess.run(cmd)
    except KeyboardInterrupt:
        print_colored("\n\n👋 Streamlit application stopped", Colors.YELLOW)
    except Exception as e:
        print_colored(f"\n❌ Error running Streamlit: {e}", Colors.RED)
        sys.exit(1)

def main():
    """Main function to run the application"""
    print_colored("\n🏁 RPM Streamlit Launcher\n", Colors.HEADER)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print_colored(f"📂 Changed to directory: {script_dir}", Colors.BLUE)
    
    # Run checks
    print_colored("\n🔍 Running pre-flight checks...\n", Colors.BLUE)
    
    check_python_version()
    
    if not check_streamlit_installed():
        print_colored("\n📦 Attempting to install Streamlit...", Colors.BLUE)
        if not install_requirements():
            print_colored("\n💡 Try running: pip install streamlit", Colors.YELLOW)
            sys.exit(1)
    
    # Check backend (warning only)
    print()
    check_backend_running()
    
    # Ask user if they want to continue
    print_colored("\n" + "="*60, Colors.BOLD)
    try:
        response = input(f"{Colors.YELLOW}▶️  Press Enter to start Streamlit (Ctrl+C to cancel)...{Colors.ENDC}")
    except KeyboardInterrupt:
        print_colored("\n\n👋 Cancelled", Colors.YELLOW)
        sys.exit(0)
    
    # Run Streamlit
    run_streamlit()

if __name__ == "__main__":
    main()
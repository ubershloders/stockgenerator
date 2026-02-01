#!/usr/bin/env python3
"""
StockMaker - Main entry point for the application
Handles Ollama startup and launches the GUI
"""

import subprocess
import time
import requests
import sys
from pathlib import Path

def is_ollama_running():
    """Check if Ollama is running and responding"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        return response.status_code == 200
    except:
        return False

def start_ollama():
    """Start Ollama service"""
    try:
        # Check if already running
        if is_ollama_running():
            print("✓ Ollama is already running")
            return True
        
        print("🚀 Starting Ollama...")
        
        # Try to start Ollama
        subprocess.Popen(['ollama', 'serve'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        
        # Wait for Ollama to start (max 30 seconds)
        for i in range(30):
            if is_ollama_running():
                print("✓ Ollama started successfully")
                return True
            print(f"  Waiting for Ollama... ({i+1}s)")
            time.sleep(1)
        
        print("⚠ Ollama startup timeout")
        return False
    except Exception as e:
        print(f"❌ Error starting Ollama: {e}")
        return False

def main():
    print("StockMaker - Stock Image CSV Generator")
    print("=" * 50)
    
    # Start Ollama
    if not start_ollama():
        print("\n⚠ Warning: Could not start Ollama")
        print("Make sure Ollama is installed: https://ollama.ai")
        # Don't prompt for GUI mode - just continue
        print("Continuing anyway...")
    
    print("\n🎨 Launching GUI...")
    
    # Import and run the GUI app
    try:
        from app_qt import main as run_gui
        run_gui()
    except ImportError as e:
        print(f"❌ Error importing GUI: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running GUI: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

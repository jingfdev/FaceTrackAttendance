#!/usr/bin/env python3
import subprocess
import sys

def install_ultralytics():
    """Install ultralytics using pip directly"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'ultralytics'])
        print("Successfully installed ultralytics")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install ultralytics: {e}")
        return False

if __name__ == "__main__":
    install_ultralytics()
"""
Download NYC Subway Traffic dataset from Kaggle.
Requires kaggle.json API token in ~/.kaggle/kaggle.json
"""

import os
import subprocess
import zipfile

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def download_dataset():
    """Download the NYC Subway Traffic 2017-21 dataset."""
    print("Downloading NYC Subway Traffic 2017-21 dataset...")
    
    # Ensure kaggle.json exists
    kaggle_json = os.path.expanduser("~/.kaggle/kaggle.json")
    if not os.path.exists(kaggle_json):
        print("ERROR: kaggle.json not found at ~/.kaggle/kaggle.json")
        print("Please download your Kaggle API token from:")
        print("https://www.kaggle.com/settings/account")
        print("and save it as ~/.kaggle/kaggle.json")
        return False
    
    # Download dataset
    os.makedirs(DATA_DIR, exist_ok=True)
    
    cmd = f"kaggle datasets download -d eddeng/nyc-subway-traffic-data-20172021 -p {DATA_DIR}"
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    
    # Unzip
    zip_path = os.path.join(DATA_DIR, "nyc-subway-traffic-data-20172021.zip")
    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(DATA_DIR)
        os.remove(zip_path)
        print("Dataset extracted successfully!")
    
    # List files
    for f in os.listdir(DATA_DIR):
        print(f"  - {f}")
    
    return True

if __name__ == "__main__":
    download_dataset()

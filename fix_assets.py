import os
from PIL import Image
import sys

def fix_assets():
    assets_dir = "c:/Projetos/MariIA/mobile/assets"
    files = ["icon.png", "splash.png", "adaptive-icon.png", "favicon.png"]
    
    for filename in files:
        path = os.path.join(assets_dir, filename)
        if not os.path.exists(path):
            print(f"Missing: {filename}")
            continue
            
        try:
            img = Image.open(path)
            print(f"{filename}: format={img.format}, mode={img.mode}")
            
            if img.format != 'PNG':
                print(f"Converting {filename} from {img.format} to PNG...")
                img.save(path, format='PNG')
                print(f"Converted {filename}")
            else:
                print(f"{filename} is already PNG.")
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")

def check_homescreen():
    path = "c:/Projetos/MariIA/mobile/src/screens/HomeScreen.js"
    if os.path.exists(path):
        print(f"HomeScreen.js exists ({os.path.getsize(path)} bytes).")
    else:
        print("HomeScreen.js MISSING!")

if __name__ == "__main__":
    fix_assets()
    check_homescreen()

#!/usr/bin/env python3
"""
Upload images to ImgBB and return URLs.
Usage: python upload_to_imgbb.py <image_path1> [image_path2] ...
"""

import sys
import os
import base64
import json

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system("pip3 install requests")
    import requests

# ImgBB API key - Get from environment or use default
IMGBB_API_KEY = os.environ.get('IMGBB_API_KEY', '0b893385aabdc7ded0fea2ee14d45156')

def upload_image(image_path: str) -> dict:
    """Upload an image to ImgBB and return the response."""
    if not os.path.exists(image_path):
        return {"error": f"File not found: {image_path}"}
    
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Upload to ImgBB
    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": IMGBB_API_KEY,
        "image": image_data,
        "name": os.path.splitext(os.path.basename(image_path))[0]
    }
    
    try:
        response = requests.post(url, data=payload, timeout=60)
        result = response.json()
        
        if result.get('success'):
            return {
                "success": True,
                "url": result['data']['url'],
                "display_url": result['data']['display_url'],
                "delete_url": result['data']['delete_url'],
                "filename": os.path.basename(image_path)
            }
        else:
            return {"error": result.get('error', 'Unknown error'), "filename": os.path.basename(image_path)}
    except Exception as e:
        return {"error": str(e), "filename": os.path.basename(image_path)}

def main():
    if len(sys.argv) < 2:
        print("Usage: python upload_to_imgbb.py <image_path1> [image_path2] ...")
        sys.exit(1)
    
    results = []
    for image_path in sys.argv[1:]:
        print(f"Uploading: {image_path}...")
        result = upload_image(image_path)
        results.append(result)
        
        if result.get('success'):
            print(f"✅ {result['filename']}: {result['url']}")
        else:
            print(f"❌ {result.get('filename', image_path)}: {result.get('error')}")
    
    # Output JSON for programmatic use
    print("\n--- JSON Output ---")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()

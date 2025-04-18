import httpx
import json
import re

# API key
getimg_key = "key-3Xg7gY6OuYiPVen7sLpcatGoOtxlRlijutFQixkUO0QsTYL02Zil1TomIUBsr1TYdP5thZ18ndT9zOmDOz8tdhK5qcyUOG2q"

# Set up headers
headers = {
    "Authorization": f"Bearer {getimg_key}",
    "Accept": "application/json"
}

try:
    # Make API call
    response = httpx.get("https://api.getimg.ai/v1/models", headers=headers)
    response.raise_for_status()
    
    # Get all models
    models = response.json()
    
    # Filter for Animagine models
    animagine_models = []
    for model in models:
        model_id = model.get('id', '').lower()
        model_name = model.get('name', '').lower()
        
        if 'animagine' in model_id or 'animagine' in model_name:
            animagine_models.append(model)
    
    # Print results
    if animagine_models:
        print(f"Found {len(animagine_models)} Animagine models:")
        for model in animagine_models:
            print("\n===== FOUND ANIMAGINE MODEL =====")
            print(f"ID: {model.get('id')}")
            print(f"Name: {model.get('name')}")
            print(f"Family: {model.get('family')}")
            print(f"Pipelines: {', '.join(model.get('pipelines', []))}")
            print("================================\n")
    else:
        # If no exact Animagine models found, try to find any model that might be similar
        anime_models = []
        for model in models:
            model_id = model.get('id', '').lower()
            model_name = model.get('name', '').lower()
            
            if any(term in model_id or term in model_name for term in ['anime', 'manga', 'japanese']):
                anime_models.append(model)
        
        if anime_models:
            print("No models with 'animagine' found, but found these anime-related models:")
            for model in anime_models:
                print(f"- ID: {model.get('id')}")
                print(f"  Name: {model.get('name')}")
                print(f"  Pipelines: {', '.join(model.get('pipelines', []))}")
                print()
        else:
            print("No Animagine or anime-related models found. Here are all available SDXL models:")
            sdxl_models = [m for m in models if m.get('family') == 'stable-diffusion-xl']
            for model in sdxl_models[:5]:  # Show just first 5 to avoid overwhelming output
                print(f"- ID: {model.get('id')}")
                print(f"  Name: {model.get('name')}")
                print()
            
            if len(sdxl_models) > 5:
                print(f"...and {len(sdxl_models) - 5} more SDXL models")
    
except Exception as e:
    print(f"Error: {e}")

import httpx
import json

# API key (provided by you)
getimg_key = "key-3Xg7gY6OuYiPVen7sLpcatGoOtxlRlijutFQixkUO0QsTYL02Zil1TomIUBsr1TYdP5thZ18ndT9zOmDOz8tdhK5qcyUOG2q"

# Set up headers
headers = {
    "Authorization": f"Bearer {getimg_key}",
    "Accept": "application/json"
}

# Make API call
try:
    response = httpx.get("https://api.getimg.ai/v1/models", headers=headers)
    
    # Check if request was successful
    response.raise_for_status()
    
    # Parse and print the JSON response
    models = response.json()
    
    # Print full response for debugging
    print("Full API Response:")
    print(json.dumps(models, indent=2))
    print("\n" + "-"*80 + "\n")
    
    # Look specifically for Animagine models
    print("Looking for Animagine models:")
    for model in models:
        if "animagine" in model.get("id", "").lower() or "animagine" in model.get("name", "").lower():
            print(f"Found Animagine model:")
            print(f"  ID: {model.get('id')}")
            print(f"  Name: {model.get('name')}")
            print(f"  Display Name: {model.get('display_name', 'N/A')}")
            print("---")
            
except Exception as e:
    print(f"Error: {e}")

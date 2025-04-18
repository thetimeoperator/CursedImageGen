import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from .env file
getimg_key = os.getenv("GETIMG_API_KEY")
print(f"API Key found: {'Yes' if getimg_key else 'No'}")

# Test API connection
api_url = "https://api.getimg.ai/v1/models"
headers = {
    "accept": "application/json",
    "authorization": f"Bearer {getimg_key}"
}

try:
    response = requests.get(api_url, headers=headers)
    print(f"Status code: {response.status_code}")
    print("Response:")
    print(response.text[:500])  # Print first 500 chars of response
    
    if response.status_code == 200:
        print("\nAPI key is valid and working!")
    else:
        print("\nAPI key issue: The API returned an error.")
        print("This is likely why your app isn't working.")
except Exception as e:
    print(f"Error connecting to API: {e}")
    print("Network connection issue or API endpoint changed.")

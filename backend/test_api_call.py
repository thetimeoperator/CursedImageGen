import os
import httpx
import asyncio
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
getimg_key = os.getenv("GETIMG_API_KEY")
print(f"Using API key: {getimg_key[:10]}...")

async def test_api():
    # Define the getimg.ai API endpoint and headers
    api_url = "https://api.getimg.ai/v1/stable-diffusion-xl/image-to-image"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {getimg_key}"
    }
    
    # Load a test image (assuming you have one in the project directory)
    try:
        # You can replace this path with any image file you have
        test_file_path = "../test_image.jpg"
        if not os.path.exists(test_file_path):
            print(f"Test image not found at {test_file_path}, using a simple string instead.")
            image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        else:
            with open(test_file_path, "rb") as f:
                contents = f.read()
                image_base64 = base64.b64encode(contents).decode('utf-8')
                print(f"Loaded image, base64 length: {len(image_base64)}")
        
        # Define the JJK style prompt
        jjk_style_prompt = (
            "Jujutsu Kaisen anime style by Studio MAPPA, "
            "with glowing blue curse energy, Shibuya arc aesthetic, "
            "dark blue and purple color palette, high-contrast shadows"
        )
        
        # Create the payload
        payload = {
            "prompt": jjk_style_prompt,
            "image": image_base64,
            "negative_prompt": "text, watermark, signature, blurry",
            "strength": 0.7,
            "steps": 30,
            "guidance": 7.5,
            "output_format": "png"
        }
        
        print("Making API call...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(api_url, json=payload, headers=headers)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("API call successful!")
                if "image" in result:
                    print(f"Got image of length: {len(result['image'])}")
                else:
                    print(f"Available keys in response: {list(result.keys())}")
            else:
                print(f"API call failed with status {response.status_code}")
                print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api())

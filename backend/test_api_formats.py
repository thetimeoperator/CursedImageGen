import os
import httpx
import asyncio
import base64
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
getimg_key = os.getenv("GETIMG_API_KEY")
print(f"Using API key: {getimg_key[:10]}...")

# Create a small test image
def create_test_image(size=(512, 512)):
    img = Image.new('RGB', size, color = (73, 109, 137))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.read()

async def test_format(format_name, image_data):
    print(f"\nTesting format: {format_name}")
    # Define the getimg.ai API endpoint and headers
    api_url = "https://api.getimg.ai/v1/stable-diffusion-xl/image-to-image"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {getimg_key}"
    }
    
    # Define the JJK style prompt
    jjk_style_prompt = (
        "Jujutsu Kaisen anime style by Studio MAPPA, "
        "with glowing blue curse energy, Shibuya arc aesthetic"
    )
    
    # Create the payload
    payload = {
        "prompt": jjk_style_prompt,
        "image": image_data,
        "negative_prompt": "text, watermark",
        "strength": 0.7,
        "steps": 10,  # using low steps for faster testing
        "guidance": 7.5,
        "output_format": "png"
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(api_url, json=payload, headers=headers)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ SUCCESS! This format works!")
                return True, format_name
            else:
                print(f"❌ Failed: {response.text}")
                return False, format_name
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return False, format_name

async def main():
    # Generate a test image
    image_bytes = create_test_image()
    
    # Test different formats:
    
    # 1. Standard base64 (no prefix)
    base64_standard = base64.b64encode(image_bytes).decode('utf-8')
    
    # 2. With data URI prefix
    base64_data_uri = f"data:image/png;base64,{base64_standard}"
    
    # 3. URL to an image (using a sample image)
    url_format = "https://docs.getimg.ai/images/flux-schnell.webp"
    
    # Run all tests
    formats = [
        ("base64_standard", base64_standard),
        ("base64_data_uri", base64_data_uri),
        ("url_format", url_format)
    ]
    
    results = []
    for name, data in formats:
        success, format_name = await test_format(name, data)
        results.append((success, format_name))
    
    # Print final results
    print("\n=== RESULTS ===")
    for success, name in results:
        status = "✅ WORKS" if success else "❌ FAILS"
        print(f"{name}: {status}")
    
    working_formats = [name for success, name in results if success]
    if working_formats:
        print(f"\nUse one of these formats: {', '.join(working_formats)}")
    else:
        print("\nNone of the tested formats worked. We may need to try other approaches.")

if __name__ == "__main__":
    asyncio.run(main())

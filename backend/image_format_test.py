import os
import base64
import httpx
import asyncio
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
getimg_key = os.getenv("GETIMG_API_KEY")
if not getimg_key:
    raise ValueError("GETIMG_API_KEY not found in .env file")

print(f"Using API key starting with: {getimg_key[:10]}...")

# Create test images of different sizes and formats
def create_test_image(size, mode="RGB", format_name="PNG"):
    # Create a simple gradient image
    width, height = size
    image = Image.new(mode, (width, height), color=(0, 0, 0))
    
    # Draw a simple pattern to make it more interesting
    for x in range(width):
        for y in range(height):
            r = int(255 * x / width)
            g = int(255 * y / height)
            b = 100
            if mode == "RGB":
                image.putpixel((x, y), (r, g, b))
            elif mode == "RGBA":
                image.putpixel((x, y), (r, g, b, 255))
    
    # Save to BytesIO
    buffer = BytesIO()
    image.save(buffer, format=format_name)
    buffer.seek(0)
    return buffer.read()

async def test_image_with_api(image_data, description):
    """Test if an image works with the API"""
    print(f"\nTesting: {description}")
    
    # Encode image as base64
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # API request parameters
    api_url = "https://api.getimg.ai/v1/stable-diffusion-xl/image-to-image"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {getimg_key}"
    }
    
    prompt = "a photo of a cat in jujutsu kaisen anime style"
    
    payload = {
        "prompt": prompt,
        "image": image_base64,
        "strength": 0.7,
        "steps": 20,
        "guidance": 7.5
    }
    
    # Try API call
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"  Making API call with image size: {len(image_data)} bytes")
            response = await client.post(api_url, json=payload, headers=headers)
            
            print(f"  Response status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS: {description} works!")
                return True, description
            else:
                error_content = response.json() if response.status_code != 500 else "Internal Server Error"
                print(f"  ❌ FAILED: {error_content}")
                return False, description
                
    except Exception as e:
        print(f"  ⚠️ ERROR: {str(e)}")
        return False, description

async def main():
    print("GETIMG.AI API FORMAT TEST")
    print("========================")
    print("Testing different image formats to find what works with getimg.ai API")
    
    test_cases = [
        # Different sizes - PNG format
        (create_test_image((256, 256)), "PNG 256x256"),
        (create_test_image((512, 512)), "PNG 512x512"),
        (create_test_image((768, 768)), "PNG 768x768"),
        (create_test_image((1024, 1024)), "PNG 1024x1024"),
        
        # Different aspect ratios
        (create_test_image((512, 768)), "PNG 512x768 (portrait)"),
        (create_test_image((768, 512)), "PNG 768x512 (landscape)"),
        
        # Different formats (all 512x512)
        (create_test_image((512, 512), format_name="JPEG"), "JPEG 512x512"),
        (create_test_image((512, 512), mode="RGBA"), "PNG with alpha channel"),
        
        # Very small image
        (create_test_image((64, 64)), "PNG tiny 64x64"),
    ]
    
    results = []
    for image_data, description in test_cases:
        success, desc = await test_image_with_api(image_data, description)
        results.append((success, desc))
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Print summary of results
    print("\n\nRESULTS SUMMARY")
    print("==============")
    successful = [desc for success, desc in results if success]
    failed = [desc for success, desc in results if not success]
    
    print(f"\n✅ SUCCESSFUL FORMATS ({len(successful)}):")
    for desc in successful:
        print(f"  - {desc}")
    
    print(f"\n❌ FAILED FORMATS ({len(failed)}):")
    for desc in failed:
        print(f"  - {desc}")
        
    if successful:
        print("\nRECOMMENDATION: Use one of the successful formats for your app.")
    else:
        print("\nNone of the tested formats worked. You may need to try different parameters.")

if __name__ == "__main__":
    asyncio.run(main())

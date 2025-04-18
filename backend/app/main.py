from fastapi import FastAPI, File, UploadFile, Form, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
import stripe, os
import httpx # Added for async HTTP requests
import base64 # Added for image encoding
from dotenv import load_dotenv
from PIL import Image # For image preprocessing
from io import BytesIO # For handling image data streams

# Load environment variables
load_dotenv()

# Initialize APIs
# Get getimg.ai API key
getimg_key = os.getenv("GETIMG_API_KEY")
if not getimg_key:
    raise ValueError("GETIMG_API_KEY not set in .env file")

stripe_key = os.getenv("STRIPE_SECRET_KEY")
if not stripe_key:
    raise ValueError("STRIPE_SECRET_KEY not set")
stripe.api_key = stripe_key

# Add Stripe Webhook Secret
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
if not stripe_webhook_secret:
    print("Warning: STRIPE_WEBHOOK_SECRET not set. Webhook verification will fail.")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app = FastAPI()
# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000", "http://127.0.0.1:50224"],
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"],
)

# Define Price Options (Map IDs to amount in cents and credits)
PRICE_OPTIONS = {
    "price_3": {"amount": 300, "credits": 10, "name": "10 Photo Credits Pack"},
    "price_10": {"amount": 1000, "credits": 50, "name": "50 Photo Credits Pack"}
}

@app.post("/api/generate")
async def generate(file: UploadFile = File(...), prompt: str = Form("")):
    """
    Receives an image and prompt, creates a Jujutsu Kaisen style version using getimg.ai's SDXL Image-to-Image API.
    """
    try:
        # 1. Read the uploaded file contents
        contents = await file.read()
        print(f"Received image file: {file.filename}, size: {len(contents)} bytes")
        
        # 1.5 Preprocess the image to ensure it meets API requirements
        try:
            # Open the image using PIL
            img = Image.open(BytesIO(contents))
            print(f"Original image dimensions: {img.size}, format: {img.format}")
            
            # Based on our tests, the API is quite flexible with image formats
            # But to be safe, let's ensure the image is in a standard format
            
            # Convert to RGB if needed (this handles RGBA or other color modes)
            if img.mode != 'RGB':
                img = img.convert('RGB')
                print(f"Converted image to RGB mode")
                
            # Our tests showed all sizes work, but let's limit to 1024x1024 max for efficiency
            if img.width > 1024 or img.height > 1024:
                img.thumbnail((1024, 1024))
                print(f"Resized image dimensions: {img.size}")
            
            # Save as PNG (most reliable from our tests)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            contents = buffered.getvalue()
            print(f"Preprocessed image: {len(contents)} bytes, PNG format")
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            # Continue with original image if preprocessing fails
            pass

        # 2. Base64 encode the image - getimg.ai requires standard base64 without data URI prefix
        image_base64 = base64.b64encode(contents).decode('utf-8')
        print(f"Encoded image to base64, length: {len(image_base64)}")

        # 3. Define the getimg.ai API endpoint and headers
        api_url = "https://api.getimg.ai/v1/stable-diffusion-xl/image-to-image"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {getimg_key}"
        }

        # 4. Define the JJK style prompt and combine with user prompt
        jjk_style_prompt = (
            "Jujutsu Kaisen anime style by Studio MAPPA, "
            "with glowing blue curse energy, Shibuya arc aesthetic, "
            "dark blue and purple color palette, high-contrast shadows with stark highlights, "
            "sharp detailed character features, dramatic lighting, bold linework, "
            "realistic cloth textures, visible energy flows, Gege Akutami art style, "
            "cinematic composition similar to Jujutsu Kaisen 0 movie"
        )
        full_prompt = f"{jjk_style_prompt}, {prompt.strip()}" if prompt and prompt.strip() else jjk_style_prompt
        negative_prompt = "text, watermark, signature, blurry, low quality, deformed, multiple limbs, extra fingers"

        # 5. Construct the payload for getimg.ai SDXL API
        # Make sure the image parameter is valid - this is critical
        if not image_base64 or len(image_base64) < 100:
            return JSONResponse(status_code=400, content={"error": "Invalid image: base64 encoding too small or empty"})
            
        # Log the image details (not the full base64 for privacy)
        print(f"Base64 image length: {len(image_base64)}, preview: {image_base64[:10]}...{image_base64[-10:]}")
        print(f"Sending to getimg.ai with prompt: '{prompt[:50]}...' (truncated)")
        
        payload = {
            "prompt": full_prompt,
            "image": image_base64,  # This is the field the API is saying is missing
            "negative_prompt": negative_prompt,
            "strength": 0.7,  # Controls how much the original image influences the result
            "steps": 30,     # Number of diffusion steps
            "guidance": 7.5,  # How closely to follow the prompt
            "output_format": "png"
        }
        
        # Verify payload has the required fields
        print(f"Payload contains image field: {'image' in payload}")
        print(f"Payload fields: {list(payload.keys())}")
        
        print(f"Calling getimg.ai SDXL API with prompt: {full_prompt[:100]}...")

        # 6. Make the asynchronous API call using httpx
        async with httpx.AsyncClient(timeout=60.0) as client: # Increased timeout for image generation
            print(f"Making API call to: {api_url}")
            # Ensure our headers are correct
            print(f"Using headers: {headers}")
            # Make the API call
            response = await client.post(api_url, json=payload, headers=headers)
            print(f"Response status: {response.status_code}")
            
            # 7. Process the response
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            result = response.json()
            print(f"API Response status: {response.status_code}")
            print(f"API Response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")            
            # 8. Extract the generated image (assuming it's in result['image'] as base64)
            generated_image_base64 = result.get('image')
            if not generated_image_base64:
                print(f"Error: 'image' field not found in getimg.ai response: {result}")
                return JSONResponse(status_code=500, content={"error": "Failed to retrieve image from API response"})
            # Ensure the base64 image format is correct (no prefix)
            if generated_image_base64.startswith('data:image/'):
                generated_image_base64 = generated_image_base64.split(',')[1]

            # 9. Return the base64 encoded image
            return JSONResponse(content={"image_base64": generated_image_base64})

    except httpx.HTTPStatusError as e:
        # Handle API errors specifically
        error_details = "Unknown API error"
        try:
            error_details = e.response.json()
        except Exception:
            error_details = e.response.text
        print(f"getimg.ai API Error: {e.response.status_code} - {error_details}")
        return JSONResponse(status_code=e.response.status_code, content={"error": f"API Error: {error_details}"})

    except Exception as e:
        # Handle other potential errors (file reading, base64 encoding, etc.)
        print(f"Error during image generation: {e}")
        import traceback
        traceback.print_exc() # Print detailed traceback for debugging
        return JSONResponse(status_code=500, content={"error": f"An unexpected error occurred: {str(e)}"})

    except Exception as e:
        # Handle any errors that occurred
        print(f"Error during image generation: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"An unexpected error occurred: {str(e)}"})


@app.get("/api/checkout")
async def checkout(price_id: str = None):
    """Redirects user to Stripe Checkout for buying credits based on price_id"""
    if price_id not in PRICE_OPTIONS:
        return JSONResponse(status_code=400, content={"error": "Invalid price option selected"})

    option = PRICE_OPTIONS[price_id]
    amount = option["amount"]
    credits_to_add = option["credits"]
    product_name = option["name"]

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": product_name},
                    "unit_amount": amount
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=f"{FRONTEND_URL}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=FRONTEND_URL,
            # Add metadata to store credits
            metadata={'credits_to_add': str(credits_to_add)} # Metadata values must be strings
        )
        return {"url": session.url}
    except Exception as e:
        print(f"Stripe Checkout Error: {e}")
        return JSONResponse(status_code=500, content={"error": "Could not create checkout session"})

@app.get("/api/confirm")
async def confirm(session_id: str):
    """Retrieve Stripe checkout session and return number of credits purchased from metadata."""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        # Check payment status
        if session.payment_status == 'paid':
            # Retrieve credits from metadata
            credits_to_add = int(session.metadata.get('credits_to_add', '0')) 
            if credits_to_add > 0:
                 print(f"Payment confirmed for session {session_id}, adding {credits_to_add} credits.")
                 return {"credits": credits_to_add}
            else:
                 print(f"Error: Payment confirmed for session {session_id} but no credits found in metadata.")
                 return {"error": "Could not determine credits purchased"}, 400
        else:
            print(f"Payment not successful for session {session_id}. Status: {session.payment_status}")
            return {"error": "Payment not successful"}, 402 # Payment Required status

    except stripe.error.InvalidRequestError as e:
         print(f"Error retrieving session {session_id}: {e}")
         return {"error": "Invalid session ID"}, 404
    except Exception as e:
         print(f"Error confirming payment for session {session_id}: {e}")
         return {"error": "Failed to confirm payment"}, 500

# Add Stripe Webhook Endpoint
@app.post("/api/stripe-webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """Listens for Stripe events (specifically checkout completion)"""
    if not stripe_webhook_secret:
        print("Webhook skipped: No secret configured.")
        return {"status": "webhook secret not configured"}
    if not stripe_signature:
        print("Webhook failed: No signature header")
        return {"status": "missing signature"}, 400

    try:
        payload = await request.body()
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, stripe_webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        print(f"Webhook ValueError: {e}")
        return {"status": "invalid payload"}, 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print(f"Webhook SignatureError: {e}")
        return {"status": "invalid signature"}, 400

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Fulfill the purchase (e.g., log it, update backend db if exists)
        # Since credits are handled client-side via /api/confirm after redirect,
        # we just log it here for confirmation.
        print(f"Payment successful (via webhook) for session: {session.id}")
        # TODO: Add any backend fulfillment logic here if needed beyond client-side credits

    else:
        print(f"Unhandled Stripe event type: {event['type']}")

    return {"status": "success"}

from fastapi import FastAPI, File, UploadFile, Form, Request, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
import stripe, os
from openai import AsyncOpenAI
import base64
import httpx
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO

# Load environment variables
load_dotenv()

# Initialize APIs
# Get OpenAI API key
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("OPENAI_API_KEY not set in .env file")

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
    Receives an image and prompt, creates a Jujutsu Kaisen style version using OpenAI's gpt-image-1 edit API.
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
            buffered.seek(0) # IMPORTANT: Reset buffer position to the beginning
            contents = buffered.getvalue() # Get raw bytes after saving as PNG
            print(f"Preprocessed image: {len(contents)} bytes, PNG format")
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            # Fallback: use original contents if preprocessing failed
            pass

        # Define filename and create the tuple for file upload
        image_filename = "uploaded_image.png"
        # Use the raw 'contents' bytes in the tuple, per SDK docs
        image_data_tuple = (image_filename, contents, "image/png")

        # Initialize OpenAI Client with custom HTTP client to disable proxy env vars
        custom_http_client = httpx.AsyncClient(trust_env=False)
        client = AsyncOpenAI(api_key=openai_key, http_client=custom_http_client)

        # 4. Define the JJK style prompt and combine with user prompt
        jjk_style_prompt = (
            "masterpiece, best quality, official Studio MAPPA artwork from Jujutsu Kaisen anime, "
            "precise crisp lineart, professional anime production quality, "
            "distinct bold black outlines, carefully cell-shaded anime art, "
            "Shibuya arc signature style, Studio MAPPA color grading with deep purple and navy accents, "
            "dramatic anime lighting with high contrast, flawless anime proportions, "
            "expert animation-cel quality, fine detailed anime illustration, "
            "authentic Gege Akutami character art, perfect anime eyes with highlights, "
            "highly detailed background art, professional anime key visual quality"
        )
        final_prompt = jjk_style_prompt + f" {prompt}" if prompt else jjk_style_prompt
        print(f"Final prompt for OpenAI: {final_prompt}")

        # 5. Call OpenAI Image Edit API
        print(f"Calling OpenAI images.edit with model gpt-image-1...")
        async with client:
            response = await client.images.edit(
                model="gpt-image-1",
                image=image_data_tuple, # Pass tuple: (filename, raw_bytes, mimetype)
                prompt=final_prompt,
                n=1,
                size="1024x1024" # Standard size
            )
        
        # 6. Process the response
        b64_image = response.data[0].b64_json
        print(f"Successfully received image from OpenAI. Size: {len(b64_image)} chars")
        # 7. Decode the base64 string to raw bytes
        image_bytes = base64.b64decode(b64_image)
        print(f"Decoded image to {len(image_bytes)} bytes")

        # 8. Return the raw image bytes with the correct media type
        return Response(content=image_bytes, media_type="image/png")

    except Exception as e: # Consider more specific OpenAI exceptions later if needed
        error_message = f"Error calling OpenAI API: {e}"
        print(error_message)
        # Consider mapping specific OpenAI errors to user-friendly messages
        status_code = 500 # Default to internal server error
        # Add checks for specific error types from OpenAI if applicable
        # e.g., if isinstance(e, openai.error.AuthenticationError): status_code = 401
        #      if isinstance(e, openai.error.RateLimitError): status_code = 429
        # Check if error has a status_code attribute (newer OpenAI client might)
        if hasattr(e, 'status_code'):
             status_code = e.status_code
        return JSONResponse(status_code=status_code, content={"error": f"Image generation failed: {str(e)}"}) 

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

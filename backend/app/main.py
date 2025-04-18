from fastapi import FastAPI, File, UploadFile, Form, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
import stripe, os
import httpx # Added for async HTTP requests
import base64 # Added for image encoding
import io
from PIL import Image
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()

# Initialize APIs
# Get Hugging Face API key
hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
if not hf_api_key:
    raise ValueError("HUGGINGFACE_API_KEY not set in .env file")

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
    allow_origins=[FRONTEND_URL],
    allow_methods=["*"],
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
    Receives an image and prompt, creates a Jujutsu Kaisen style version using Hugging Face's Inference API.
    """
    try:
        # 1. Read the uploaded file contents
        contents = await file.read()

        # 2. Define the JJK style prompt and combine with user prompt
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

        print(f"Using Hugging Face Inference API with prompt: {full_prompt[:100]}...")
        
        # 3. Initialize the Hugging Face Inference Client
        client = InferenceClient(api_key=hf_api_key)
        
        # 4. Create a PIL Image from the uploaded bytes
        input_image = Image.open(io.BytesIO(contents))
        
        # 5. Call the Hugging Face Inference API for image-to-image generation
        # Using the cagliostrolab/animagine-xl-3.1 model
        result_image = client.image_to_image(
            image=input_image,
            prompt=full_prompt,
            negative_prompt=negative_prompt,
            model="cagliostrolab/animagine-xl-3.1",
            # Additional parameters for the model
            guidance_scale=7.5,  # How closely to follow the prompt
            strength=0.7,        # Controls how much the original image influences the result
            num_inference_steps=30  # Number of diffusion steps
        )
        
        print("Successfully generated image with Hugging Face API")
        
        # 6. Convert the PIL Image to base64 for sending to frontend
        buffered = io.BytesIO()
        result_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # 7. Return the base64 encoded image
        return JSONResponse(content={"image_base64": img_str})

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

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import openai, stripe, os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize APIs
oai_key = os.getenv("OPENAI_API_KEY")
if not oai_key:
    raise ValueError("OPENAI_API_KEY not set")
openai.api_key = oai_key

stripe_key = os.getenv("STRIPE_SECRET_KEY")
if not stripe_key:
    raise ValueError("STRIPE_SECRET_KEY not set")
stripe.api_key = stripe_key

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app = FastAPI()
# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/generate")
async def generate(file: UploadFile = File(...), prompt: str = Form("")):
    """
    Receives an image and optional prompt, returns a generated Jujutsu Kaisen–style image URL.
    For testing, credits are NOT checked.
    """
    try:
        # Read the uploaded file (not used in OpenAI API, but could be for future custom models)
        _ = await file.read()
        # Always prepend the prompt for JJK style
        full_prompt = f"{prompt.strip()} in the style of Jujutsu Kaisen, Studio Mappa anime, highly detailed, vibrant colors, dramatic lighting"
        resp = openai.Image.create(
            prompt=full_prompt,
            n=1,
            size="512x512"
        )
        url = resp["data"][0]["url"]
        return {"url": url}
    except Exception as e:
        print(f"Image generation failed: {e}")
        return {"error": str(e)}, 500

@app.get("/api/checkout")
async def checkout():
    """Redirects user to Stripe Checkout for buying credits"""
    # Price amount in cents, default $5
    amount = int(os.getenv("PRICE_AMOUNT", "500"))
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "Photo Credits Pack"},
                "unit_amount": amount
            },
            "quantity": 1
        }],
        mode="payment",
        success_url=f"{FRONTEND_URL}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=FRONTEND_URL,
    )
    return RedirectResponse(session.url)

# CursedImageGen
Jujutsu Kaisen style image-to-image transformation app

## Project Scope
- A single-page React app allowing users to upload a photo and generate a Jujutsu Kaisen–style image via the OpenAI `gpt-image-1` API (DALL-E 3 backend).
- Users purchase credit packages (popcorn model): 1 credit = 1 photo generation, $3 for 10 generations, $10 for 50 generations via Stripe Checkout.
- Users purchase credit packages (popcorn model): 1 credit = 1 photo generation, $3 for 10 generations, $10 for 50 generations via Stripe Checkout.
- No user accounts; credits and generated images persist in browser `localStorage` per client.
- UI: upload + prompt form, Generate button, credit balance display, Buy Credits button, and gallery of previous generations with download options.

## Tech Stack
- Frontend: React (Create React App)
- Backend: FastAPI, Uvicorn
- Image Generation: OpenAI `gpt-image-1` Image Edit API (`images.edit`)
- Payment Processing: Stripe API
- HTTP Client: `openai` Python library
- Env: `python-dotenv`
- Persistence: Browser `localStorage`

## Current Implementation
- Backend uses OpenAI's `gpt-image-1` model via the `images.edit` endpoint for high-quality anime-style transformations based on input images.
- Custom JJK-style prompt that incorporates Studio MAPPA aesthetics, blue curse energy, and Shibuya arc visuals, combined with the input image.
- Frontend displays generated images as base64 and includes download buttons
- API key stored in `.env` file (requires `OPENAI_API_KEY`)
- Stripe integration for purchasing credits
- Credits and generated images stored in localStorage

## File Structure
```
Jujutsu Kaisen Photo Gen App/
├─ README.md
├─ .gitignore
├─ .env (contains API keys, requires `OPENAI_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`)
├─ frontend/
│  ├─ package.json
│  └─ src/
│     ├─ App.jsx (main application component)
│     ├─ index.js
│     ├─ assets/
│     └─ index.css
└─ backend/
   ├─ requirements.txt
   └─ app/
      ├─ main.py (FastAPI server with image generation and payment endpoints)

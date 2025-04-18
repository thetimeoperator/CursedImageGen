# CursedImageGen
Jujutsu Kaisen style image-to-image transformation app

## Project Scope
- A single-page React app allowing users to upload a photo and generate a Jujutsu Kaisen–style image via the Hugging Face Inference API with the cagliostrolab/animagine-xl-3.1 model.
- Users purchase credit packages (popcorn model): 1 credit = 1 photo generation, $3 for 10 generations, $10 for 50 generations via Stripe Checkout.
- No user accounts; credits and generated images persist in browser `localStorage` per client.
- UI: upload + prompt form, Generate button, credit balance display, Buy Credits button, and gallery of previous generations with download options.

## Tech Stack
- Frontend: React (Create React App)
- Backend: FastAPI, Uvicorn
- Image Generation: Hugging Face Inference API (cagliostrolab/animagine-xl-3.1 model)
- Payment Processing: Stripe API
- HTTP Client: huggingface_hub for API calls
- Env: `python-dotenv`
- Persistence: Browser `localStorage`

## Current Implementation
- Backend uses Hugging Face's Inference API for image-to-image transformation with the Animagine v3.1 model
- Custom JJK-style prompt that incorporates Studio MAPPA aesthetics, blue curse energy, and Shibuya arc visuals
- Frontend displays generated images as base64 and includes download buttons
- API key stored in .env file
- Stripe integration for purchasing credits
- Credits and generated images stored in localStorage

## File Structure
```
Jujutsu Kaisen Photo Gen App/
├─ README.md
├─ .gitignore
├─ .env (contains API keys)
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
```

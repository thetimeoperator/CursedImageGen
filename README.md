# Jujutsu Kaisen Photo Gen App

## Project Scope
- A single-page React app allowing users to upload a photo and generate a Jujutsu Kaisen–style image via the ChatGPT 4o image generation API.
- Users purchase credit packages (popcorn model): $5 for 10 generations, $10 for 30, $20 for 75 via Stripe Checkout.
- No user accounts; credits and generated images persist in browser `localStorage` per client.
- UI: upload + prompt form, Generate button, credit balance display, Buy Photos button, and gallery of previous generations.

## Tech Stack
- Frontend: React (Create React App), CSS Modules
- Backend: FastAPI, Uvicorn
- SDKs: OpenAI Python SDK, Stripe Python SDK
- Env: `python-dotenv`
- Persistence: Browser `localStorage`
- Deployment: Frontend (Vercel/Netlify), Backend (Heroku/Render)

## Proposed File Structure
```
Jujutsu Kaisen Photo Gen App/
├─ README.md
├─ .gitignore
├─ .env.example
├─ frontend/
│  ├─ package.json
│  └─ src/
│     ├─ App.jsx
│     ├─ index.js
│     ├─ components/
│     ├─ assets/
│     └─ styles/
└─ backend/
   ├─ requirements.txt
   └─ app/
      ├─ main.py
      ├─ api/
      ├─ core/
      ├─ models/
      ├─ schemas/
      └─ utils/
```

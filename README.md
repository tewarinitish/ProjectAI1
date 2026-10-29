# AI Try-On (mobile web app)

Upload a person photo + a garment photo, tap **Create**, get the person wearing it.
Uses the IDM-VTON model on Replicate (pay per run, no GPU needed on your side).

## Run locally
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    export REPLICATE_API_TOKEN=r8_xxx      # from replicate.com/account/api-tokens
    uvicorn app:app --host 0.0.0.0 --port 8000

Open http://localhost:8000. To test on your phone, use your computer's LAN IP
(e.g. http://192.168.1.20:8000) on the same Wi-Fi.

## Deploy
Any host that runs Python works (Render, Railway, Fly.io, a VPS).
Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
Set `REPLICATE_API_TOKEN` as an environment variable. Use HTTPS in production.

## Before going public
- Add login or rate limiting. Each Create click costs you money.
- Tell users how photos are handled. This code keeps nothing on disk, but Replicate processes the images.
- This model is for clothing only (tops, bottoms, dresses). It is not trained for jewellery.

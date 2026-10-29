"""AI virtual try-on server. Serves the mobile page and one API route."""
import io
import os

import httpx
import replicate
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps

MODEL = os.getenv(
    "TRYON_MODEL",
    "cuuupid/idm-vton:c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
)
CATEGORIES = {"upper_body", "lower_body", "dresses"}
MAX_SIDE = 1024
MAX_BYTES = 12 * 1024 * 1024

app = FastAPI()


def prepare(raw: bytes) -> io.BytesIO:
    """Fix phone rotation, shrink, and re-encode as JPEG."""
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    except Exception:
        raise HTTPException(400, "One of the files is not a readable image.")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=92)
    buf.seek(0)
    buf.name = "image.jpg"
    return buf


@app.post("/api/tryon")
def tryon(
    person: UploadFile = File(...),
    garment: UploadFile = File(...),
    category: str = Form("upper_body"),
    description: str = Form("clothing"),
):
    if category not in CATEGORIES:
        raise HTTPException(400, "Unknown category.")
    p, g = person.file.read(), garment.file.read()
    if len(p) > MAX_BYTES or len(g) > MAX_BYTES:
        raise HTTPException(413, "Image too large (12 MB max).")
    try:
        output = replicate.run(
            MODEL,
            input={
                "human_img": prepare(p),
                "garm_img": prepare(g),
                "garment_des": description.strip()[:120] or "clothing",
                "category": category,
                "crop": True,   # lets non 3:4 phone photos work
                "steps": 30,
            },
        )
    except Exception as e:
        raise HTTPException(502, f"The AI service failed: {e}")

    # Output is a file-like object or a URL depending on client version.
    if hasattr(output, "read"):
        data = output.read()
    else:
        data = httpx.get(str(output), timeout=60).content
    out = io.BytesIO()
    Image.open(io.BytesIO(data)).convert("RGB").save(out, "JPEG", quality=92)
    return Response(out.getvalue(), media_type="image/jpeg")


@app.get("/")
def index():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")

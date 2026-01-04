import os
from io import BytesIO
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from PIL import Image

from clip_retrieval.clip_wrapper import ClipEmbedder
from clip_retrieval.weaviate_store import WeaviateStore


class SearchRequest(BaseModel):
    text: str
    limit: int = 5


class SearchResult(BaseModel):
    streamer_id: str
    image_uri: str
    distance: Optional[float] = None
    id: Optional[str] = None


app = FastAPI(title="CLIP Retrieval API")

weaviate_url = os.environ.get("WEAVIATE_URL", "http://localhost:8080")
weaviate_api_key = os.environ.get("WEAVIATE_API_KEY")
image_dir = os.environ.get("IMAGE_DIR", "data/streamer_images")

store = WeaviateStore(url=weaviate_url, api_key=weaviate_api_key)
store.ensure_schema()
embedder = ClipEmbedder()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/streamers")
async def add_streamer(
    streamer_id: str = Form(...),
    image: UploadFile = File(...),
) -> dict:
    if not streamer_id.strip():
        raise HTTPException(status_code=400, detail="streamer_id is required")

    os.makedirs(image_dir, exist_ok=True)
    filename = f"{streamer_id}_{image.filename}"
    image_path = os.path.join(image_dir, filename)

    contents = await image.read()
    try:
        pil_image = Image.open(BytesIO(contents)).convert("RGB")
    except OSError as exc:
        raise HTTPException(status_code=400, detail="invalid image file") from exc

    pil_image.save(image_path)
    vector = embedder.encode_image([pil_image])[0]
    object_id = store.add_streamer(streamer_id, image_path, vector)

    return {"id": object_id, "streamer_id": streamer_id, "image_uri": image_path}


@app.post("/search", response_model=List[SearchResult])
def search(request: SearchRequest) -> List[SearchResult]:
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    query_vector = embedder.encode_text([request.text])[0]
    results = store.query_by_vector(query_vector, limit=request.limit)
    return [
        SearchResult(
            streamer_id=item.get("streamer_id", ""),
            image_uri=item.get("image_uri", ""),
            distance=item.get("_additional", {}).get("distance"),
            id=item.get("_additional", {}).get("id"),
        )
        for item in results
    ]

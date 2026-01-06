import json
import os
from io import BytesIO
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen

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
    score: Optional[float] = None
    id: Optional[str] = None


app = FastAPI(title="CLIP Retrieval API")

weaviate_url = os.environ.get("WEAVIATE_URL", "http://10.68.200.131:18080")
weaviate_api_key = os.environ.get("WEAVIATE_API_KEY")
weaviate_grpc_port = os.environ.get("WEAVIATE_GRPC_PORT")
grpc_port = int(weaviate_grpc_port) if weaviate_grpc_port else None
clip_model = os.environ.get("CLIP_MODEL", "openai/clip-vit-large-patch14")
image_dir = os.environ.get("IMAGE_DIR", "data/streamer_images")

store = WeaviateStore(url=weaviate_url, api_key=weaviate_api_key, grpc_port=grpc_port)
store.ensure_schema()
embedder = ClipEmbedder(model_name=clip_model)


@app.on_event("shutdown")
def shutdown() -> None:
    # Ensure the Weaviate client connection is closed cleanly.
    store.client.close()


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
            score=item.get("_additional", {}).get("score"),
            id=item.get("_additional", {}).get("id"),
        )
        for item in results
    ]


@app.get("/debug/streamers")
def debug_streamers(
    streamer_id: Optional[str] = None,
    limit: int = 1,
    include_vector: bool = True,
) -> Dict[str, Any]:
    fields = "streamer_id image_uri _additional { id"
    if include_vector:
        fields += " vector"
    fields += " }"

    where = ""
    if streamer_id:
        safe_id = streamer_id.replace('"', '\\"')
        where = f'where:{{path:["streamer_id"], operator:Equal, valueText:"{safe_id}"}}'

    query = f"{{ Get {{ Streamer(limit:{limit} {where}) {{ {fields} }} }} }}"
    payload = json.dumps({"query": query}).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    if weaviate_api_key:
        headers["Authorization"] = f"Bearer {weaviate_api_key}"

    request = Request(f"{weaviate_url}/v1/graphql", data=payload, headers=headers)
    try:
        with urlopen(request, timeout=10) as response:
            data = response.read().decode("utf-8")
            return json.loads(data)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

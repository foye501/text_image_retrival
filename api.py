import json
import logging
import os
from io import BytesIO
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

import boto3
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from PIL import Image
from dotenv import load_dotenv

from clip_retrieval.clip_wrapper import ClipEmbedder
from clip_retrieval.weaviate_store import WeaviateStore


class SearchRequest(BaseModel):
    text: str
    limit: int = 5
    streamer_id: Optional[str] = None


class SearchResult(BaseModel):
    streamer_id: str
    image_uri: str
    distance: Optional[float] = None
    score: Optional[float] = None
    id: Optional[str] = None


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clip_api")
app = FastAPI(title="CLIP Retrieval API")

weaviate_url = os.environ.get("WEAVIATE_URL", "http://10.68.200.131:18080")
weaviate_api_key = os.environ.get("WEAVIATE_API_KEY")
weaviate_grpc_port = os.environ.get("WEAVIATE_GRPC_PORT")
grpc_port = int(weaviate_grpc_port) if weaviate_grpc_port else None
clip_model = os.environ.get("CLIP_MODEL", "openai/clip-vit-large-patch14")
image_dir = os.environ.get("IMAGE_DIR", "data/streamer_images")
s3_bucket = os.environ.get("S3_BUCKET")
s3_region = os.environ.get("S3_REGION")
s3_access_key = os.environ.get("S3_ACCESS_KEY_ID")
s3_secret_key = os.environ.get("S3_SECRET_ACCESS_KEY")
s3_presign_expires = int(os.environ.get("S3_PRESIGN_EXPIRES", "3600"))

store = WeaviateStore(url=weaviate_url, api_key=weaviate_api_key, grpc_port=grpc_port)
store.ensure_schema()
embedder = ClipEmbedder(model_name=clip_model)
s3_client = None
if s3_bucket and s3_access_key and s3_secret_key:
    s3_client = boto3.client(
        "s3",
        region_name=s3_region,
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
    )


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
    image: Optional[UploadFile] = File(None),
    s3_key: Optional[str] = Form(None),
    presigned_url: Optional[str] = Form(None),
) -> dict:
    if not streamer_id.strip():
        raise HTTPException(status_code=400, detail="streamer_id is required")

    if image is None and not s3_key and not presigned_url:
        raise HTTPException(
            status_code=400,
            detail="image, s3_key, or presigned_url is required",
        )

    contents = None
    image_uri = None
    if s3_key:
        if not s3_client or not s3_bucket:
            raise HTTPException(status_code=400, detail="S3 is not configured")
        try:
            presigned = s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": s3_bucket, "Key": s3_key},
                ExpiresIn=s3_presign_expires,
            )
            with urlopen(presigned, timeout=15) as response:
                contents = response.read()
            image_uri = s3_key
        except Exception as exc:
            logger.exception("S3 download failed")
            raise HTTPException(status_code=502, detail=f"S3 download failed: {exc}") from exc
    elif image is not None:
        os.makedirs(image_dir, exist_ok=True)
        filename = f"{streamer_id}_{image.filename}"
        image_path = os.path.join(image_dir, filename)
        contents = await image.read()
        image_uri = image_path
    else:
        try:
            with urlopen(presigned_url, timeout=15) as response:
                contents = response.read()
            parsed = urlparse(presigned_url)
            image_uri = parsed.path.lstrip("/")
        except Exception as exc:
            logger.exception("Presigned URL download failed")
            raise HTTPException(
                status_code=502,
                detail=f"Presigned URL download failed: {exc}",
            ) from exc
    try:
        pil_image = Image.open(BytesIO(contents)).convert("RGB")
    except OSError as exc:
        raise HTTPException(status_code=400, detail="invalid image file") from exc

    vector = embedder.encode_image([pil_image])[0]
    object_id = store.add_streamer(streamer_id, image_uri, vector)

    return {"id": object_id, "streamer_id": streamer_id, "image_uri": image_uri}


class DeleteRequest(BaseModel):
    streamer_id: Optional[str] = None
    s3_key: Optional[str] = None
    image_uri: Optional[str] = None


@app.post("/streamers/delete")
def delete_streamer_post(request: DeleteRequest) -> Dict[str, Any]:
    if not request.streamer_id and not request.s3_key and not request.image_uri:
        raise HTTPException(
            status_code=400,
            detail="streamer_id, s3_key, or image_uri is required",
        )

    resolved_uri = request.image_uri
    if request.s3_key:
        resolved_uri = request.s3_key

    try:
        return store.delete_streamers(
            streamer_id=request.streamer_id,
            image_uri=resolved_uri,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/search", response_model=List[SearchResult])
def search(request: SearchRequest) -> List[SearchResult]:
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    query_vector = embedder.encode_text([request.text])[0]
    results = store.query_by_vector(
        query_vector,
        limit=request.limit,
        streamer_id=request.streamer_id,
    )
    return [
        SearchResult(
            streamer_id=item.get("streamer_id", ""),
            image_uri=item.get("image_uri", ""),
            distance=item.get("_additional", {}).get("distance"),
            score=(
                item.get("_additional", {}).get("score")
                if item.get("_additional", {}).get("score") is not None
                else (
                    None
                    if item.get("_additional", {}).get("distance") is None
                    else 1.0 - item.get("_additional", {}).get("distance")
                )
            ),
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

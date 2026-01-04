# CLIP Text-Image Retrieval (Weaviate)

Minimal wrapper around a transformer CLIP model to store streamer image vectors in Weaviate and query by text.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
export WEAVIATE_URL="http://localhost:8080"
export WEAVIATE_API_KEY="your-api-key-if-needed"
export IMAGE_DIR="data/streamer_images"
python main.py
```

## Run API

```bash
export WEAVIATE_URL="http://localhost:8080"
export WEAVIATE_API_KEY="your-api-key-if-needed"
export IMAGE_DIR="data/streamer_images"
uvicorn api:app --reload
```

## Example API calls

```bash
# Add streamer image
curl -X POST "http://127.0.0.1:8000/streamers" \
  -F "streamer_id=streamer_001" \
  -F "image=@/path/to/streamer_001.jpg"

# Search by text
curl -X POST "http://127.0.0.1:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"text":"streamer with neon background","limit":3}'
```

## Notes

- The Weaviate class is created with `vectorizer: "none"` since embeddings come from CLIP.
- Replace the example `streamers` list in `main.py` with your ingestion pipeline.

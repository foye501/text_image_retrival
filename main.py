import os

from clip_retrieval.clip_wrapper import ClipEmbedder
from clip_retrieval.weaviate_store import WeaviateStore


def main() -> None:
    weaviate_url = os.environ.get("WEAVIATE_URL", "http://10.68.200.131:18080")
    weaviate_api_key = os.environ.get("WEAVIATE_API_KEY")
    weaviate_grpc_port = os.environ.get("WEAVIATE_GRPC_PORT")
    grpc_port = int(weaviate_grpc_port) if weaviate_grpc_port else None
    clip_model = os.environ.get("CLIP_MODEL", "openai/clip-vit-large-patch14")

    store = WeaviateStore(url=weaviate_url, api_key=weaviate_api_key, grpc_port=grpc_port)
    store.ensure_schema()

    clip = ClipEmbedder(model_name=clip_model)

    # Example: add streamer images (replace with your own data ingestion).
    streamers = [
        {"id": "streamer_001", "image_path": "data/streamer_001.jpg"},
        {"id": "streamer_002", "image_path": "data/streamer_002.jpg"},
    ]
    for streamer in streamers:
        vector = clip.encode_image([streamer["image_path"]])[0]
        store.add_streamer(streamer["id"], streamer["image_path"], vector)

    # Example: query by text.
    query = "a streamer with a headset and neon background"
    query_vector = clip.encode_text([query])[0]
    results = store.query_by_vector(query_vector, limit=3)

    for match in results:
        print(match)


if __name__ == "__main__":
    main()

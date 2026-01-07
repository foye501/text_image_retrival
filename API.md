# CLIP Retrieval API

Base URL:

```
http://<host>:<port>
```

## Health

`GET /health`

Response:

```json
{"status":"ok"}
```

## Add Streamer Image

`POST /streamers`

Content-Type: `multipart/form-data`

Fields:

- `streamer_id` (string)
- `image` (file, optional if `s3_key` provided)
- `s3_key` (string, optional if `image` provided)

Response:

```json
{
  "id": "uuid",
  "streamer_id": "streamer_001",
  "image_uri": "data/streamer_images/streamer_001.jpg"
}
```

Example:

```bash
curl -X POST "http://<host>:<port>/streamers" \
  -F "streamer_id=streamer_001" \
  -F "image=@/path/to/streamer_001.jpg"
```

Example (S3):

```bash
curl -X POST "http://<host>:<port>/streamers" \
  -F "streamer_id=streamer_001" \
  -F "s3_key=path/to/streamer_001.jpg"
```

## Search by Text

`POST /search`

Content-Type: `application/json`

Body:

```json
{"text":"a streamer with neon background","limit":3}
```

Response:

```json
[
  {
    "streamer_id": "streamer_001",
    "image_uri": "data/streamer_images/streamer_001.jpg",
    "distance": 0.75,
    "score": 0.25,
    "id": "uuid"
  }
]
```

Example:

```bash
curl -X POST "http://<host>:<port>/search" \
  -H "Content-Type: application/json" \
  -d '{"text":"a streamer with neon background","limit":3,"streamer_id":"streamer_001"}'
```

## Debug: List Streamers

`GET /debug/streamers`

Query params:

- `streamer_id` (optional)
- `limit` (default: `1`)
- `include_vector` (default: `true`)

Example:

```bash
curl "http://<host>:<port>/debug/streamers?limit=1&include_vector=true"
```

## OpenAPI

- `GET /docs` (Swagger UI)
- `GET /openapi.json`

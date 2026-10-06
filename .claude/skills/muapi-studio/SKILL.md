---
name: muapi-studio
description: Generate AI images, videos and lip-sync clips through Muapi.ai's 220+ models (Nano Banana, Flux, Seedream, Midjourney, GPT-4o, Kling, Veo 3/3.1, Sora, Wan, Seedance, Hailuo, Infinite Talk, LatentSync…). The engine behind Open Higgsfield AI, used here directly from the CLI. Use when the user wants to generate or edit an image, make a video from text or an image, animate a portrait, or lip-sync a face to audio, and wants Muapi / Open Higgsfield rather than another provider.
allowed-tools: Bash, Read
---

# Muapi Studio (Open Higgsfield AI engine)

Headless port of [Open Higgsfield AI](https://github.com/Anil-matcha/Open-Higgsfield-AI) (MIT): the same Muapi.ai API and model catalog, without the web UI. `SKILL_DIR` is the directory containing this file.

```bash
python3 "$SKILL_DIR/scripts/muapi.py" --help
```

The script uses only the Python standard library.

## Setup

- **API key** — read from `MUAPI_API_KEY`, then `~/.config/muapi/.env` (`MUAPI_API_KEY=...`). Keys come from https://muapi.ai (paid, per-generation credits). Exit code 3 means no key. Never print the key, put it in a command line, or commit it. If the user has none, point them to https://muapi.ai and ask them to set the variable (in a cloud session: the environment's environment variables).
- **Network** — needs `api.muapi.ai` plus the CDN hosts in result URLs. Exit code 4 (`cannot reach`) means the network policy blocks it; tell the user to allow `api.muapi.ai` (and `muapi.ai`) in the environment's network settings.
- **Cost** — every `run` spends the user's credits, video models much more than images. Confirm the model and settings before generating, and before batch or repeated runs.

## Model types

| type | meaning | key payload fields |
|---|---|---|
| `t2i` | text → image | `prompt`, `aspect_ratio`, sometimes `resolution` / `quality` / `width`+`height` / `num_images` |
| `i2i` | image(s) → image (edit, style, upscale) | image field (see below), optional `prompt` |
| `t2v` | text → video | `prompt`, `aspect_ratio`, `duration`, `resolution`, `quality`, `mode` |
| `i2v` | start image → video | image field, `prompt`, `duration`, … |
| `lipsync` | portrait image + audio, or video + audio → talking video | `audio_url` + `image_url` (category `image`) or `video_url` (category `video`), optional `prompt`, `resolution`, `seed` |
| `v2v` | video → video | `video_url` |

**Image field:** each i2i/i2v model has an `imageField` in the catalog. If it is `images_list`, send a JSON array (`-p 'images_list=["https://…"]'`, up to `maxImages`). Otherwise send a single URL under that exact field name (`image_url`, `model_image_url`, `person_image_url`).

## Workflow

1. **Pick a model.** `muapi.py models --type t2v --query kling` lists the catalog (`references/models.json`). If the user names no model, suggest 2–3 that fit. Good defaults: `nano-banana-2` or `flux-dev` (image), `nano-banana-2-edit` (multi-image edit), `veo3.1-fast-text-to-video` / `kling-v2.6-pro-t2v` (video), `veo3.1-fast-image-to-video` (image→video), `infinitetalk-image-to-video` (talking portrait).
2. **Read its inputs.** Run `muapi.py info MODEL_ID` and use only the listed fields, respecting `enum`, `minValue`/`maxValue` and defaults.
3. **Upload local media.** For local images, video or audio, run `muapi.py upload FILE`; it prints a hosted URL to pass in the payload. Public `https://` URLs can be passed directly.
4. **Generate.**
   ```bash
   python3 "$SKILL_DIR/scripts/muapi.py" run nano-banana-2 \
     -p prompt="A neon-lit ramen bar at night, cinematic" -p aspect_ratio=16:9 -p resolution=2K \
     --out ./generated
   ```
   Values are parsed as JSON when possible (`-p duration=5`, `-p 'images_list=["…","…"]'`). Pass `--json payload.json` for large payloads. The script submits the job, polls until it finishes (5 min timeout for images, 30 min for video), prints `{request_id, status, urls, files}` and downloads the outputs into `--out`.
5. **Long jobs.** Use `--no-wait` to get the `request_id` immediately, then `muapi.py result REQUEST_ID --out DIR` later. On a timeout, the script prints the exact `result` command to resume the job without paying again.
6. **Report back.** Give the user the output file paths and/or URLs, plus the model and settings used. Result URLs are hosted by Muapi and may expire, so download anything worth keeping.

## Notes

- Payload fields mirror the app: images get `prompt`, `aspect_ratio`, `resolution`, `quality` and `seed`. Videos add `duration` and `mode`. Lip sync uses `audio_url` + `image_url`/`video_url`. Unknown model ids are sent as raw endpoints (`/api/v1/<id>`), for models newer than the catalog.
- If the API rejects a field (HTTP 4xx), show the error and adjust the payload rather than retrying blindly.
- Respect content rules: no sexual content involving minors, no non-consensual likeness of real people, and no deceptive deepfakes of real people. Lip-syncing a real person's face needs their consent. Don't strip watermarks from media the user doesn't own.

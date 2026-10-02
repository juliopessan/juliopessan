"""Testes do provider Higgsfield (Kling 3.0 / Wan 3.0), sem tocar na API.

Um transporte HTTP falso responde no lugar do serviço. A API real não foi
alcançada daqui (higgsfield.ai fica fora do egress do ambiente de dev): o que
é inferido — caminho do Wan, campos do corpo, formato do resultado — está
descrito no docstring do provider.

Roda offline: `python3 tests_higgsfield.py`.
"""
from __future__ import annotations

import os
import tempfile

os.environ.setdefault("VF_STORAGE_DIR", tempfile.mkdtemp(prefix="vf-hf-"))

import httpx  # noqa: E402

from app import config  # noqa: E402
from app.providers import PROVIDERS, capabilities  # noqa: E402
from app.providers.base import MediaInput, ProviderError, VideoRequest  # noqa: E402
from app.providers.higgsfield import (  # noqa: E402
    HiggsfieldProvider, clamp_seconds, find_video_url,
)
import app.providers.higgsfield as hf_module  # noqa: E402

failures: list[str] = []
calls: list[httpx.Request] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    print(f"{'ok  ' if condition else 'FALHA'} {label}{'' if condition else ' -> ' + detail}")
    if not condition:
        failures.append(label)


def make(**kwargs) -> HiggsfieldProvider:
    return HiggsfieldProvider(key_id="kid", key_secret="ksecret", **kwargs)


# ----------------------------------------------------------------- registro
check("registrado em PROVIDERS", PROVIDERS.get("higgsfield") is HiggsfieldProvider)
caps = capabilities("higgsfield")
check("não estende: pipeline encadeia por keyframe", caps["extend"] is False)
check("aceita 16:9, 9:16 e 1:1", caps["aspect_ratios"] == ["16:9", "9:16", "1:1"], str(caps))

# ------------------------------------------------------------- credenciais
try:
    HiggsfieldProvider(key_id="", key_secret="")
    check("sem credencial é recusado", False, "não levantou")
except ProviderError as exc:
    check("sem credencial é recusado", "HIGGSFIELD_KEY_ID" in str(exc), str(exc))
for kwargs, needle in (({"model": "sora"}, "desconhecido"), ({"tier": "ultra"}, "inválido")):
    try:
        make(**kwargs)
        check(f"recusa {needle}", False, "não levantou")
    except ProviderError as exc:
        check(f"recusa {needle}", needle in str(exc), str(exc))

# ---------------------------------------------------------------- endpoints
kling = make(tier="pro")
check("Kling usa o caminho confirmado", kling.endpoint() == "https://api.higgsfield.ai/kling-video/v3.0/pro/text-to-video", kling.endpoint())
check("Kling image-to-video troca o sufixo", kling.endpoint(image=True).endswith("/v3.0/pro/image-to-video"))
check("tier 4k", make(tier="4k").endpoint().endswith("/v3.0/4k/text-to-video"))
check("Wan 3.0 tem caminho próprio", make(model="wan-3.0").endpoint().endswith("/wan/v3.0/text-to-video"), make(model="wan-3.0").endpoint())
check("VF_HIGGSFIELD_PATH sobrescreve", make(path="/custom/x/text-to-video/").endpoint() == "https://api.higgsfield.ai/custom/x/text-to-video")
check("Authorization é Key id:secret", kling.headers["Authorization"] == "Key kid:ksecret", kling.headers["Authorization"])

# ------------------------------------------------------------------ corpo
body = kling.build_payload(VideoRequest(prompt=" Um peixe ", mode="text_to_video", duration_seconds=40, aspect_ratio="9:16"))
check("duração do Kling limitada a 15 s", body["duration"] == 15, str(body))
check("prompt aparado e proporção repassada", body["prompt"] == "Um peixe" and body["aspect_ratio"] == "9:16", str(body))
check("Kling não manda resolution", "resolution" not in body, str(body))
check("limites de duração", [clamp_seconds("kling-3.0", n) for n in (1, 8, 20)] == [3, 8, 15] and [clamp_seconds("wan-3.0", n) for n in (1, 8, 99)] == [2, 8, 30])
wan = make(model="wan-3.0").build_payload(VideoRequest(prompt="x", mode="text_to_video", resolution="1080p", duration_seconds=25))
check("Wan aceita até 30 s e manda resolution", wan["duration"] == 25 and wan["resolution"] == "1080p", str(wan))
check("Wan cai em 720p se a resolução não existe", make(model="wan-3.0").build_payload(VideoRequest(prompt="x", mode="text_to_video", resolution="360p"))["resolution"] == "720p")
frames = kling.build_payload(VideoRequest(prompt="x", mode="interpolate", media=[
    MediaInput("image", b"A", "image/png", "first_frame"), MediaInput("image", b"B", "image/png", "last_frame")]))
check("first/last frame viram image_url e end_image_url",
      frames["image_url"].startswith("data:image/png;base64,") and frames["end_image_url"].startswith("data:image/png;base64,"), str(list(frames)))
try:
    kling.build_payload(VideoRequest(prompt="x", mode="text_to_video", aspect_ratio="21:9"))
    check("proporção fora da lista é recusada", False, "não levantou")
except ProviderError as exc:
    check("proporção fora da lista é recusada", "21:9" in str(exc), str(exc))
try:
    kling.generate(VideoRequest(prompt="x", mode="extend", previous_interaction_id="r1"))
    check("extend é recusado com orientação", False, "não levantou")
except ProviderError as exc:
    check("extend é recusado com orientação", "keyframe" in str(exc), str(exc))

# ------------------------------------------------- extração da URL do vídeo
for shape, job in {
    "video.url": {"video": {"url": "https://cdn/a.mp4"}},
    "videos[].url": {"videos": [{"url": "https://cdn/a.mp4"}]},
    "results[].raw.url": {"results": [{"raw": {"url": "https://cdn/a.mp4"}}]},
    "output.video.url": {"output": {"video": {"url": "https://cdn/a.mp4"}}},
    "output string": {"output": "https://cdn/a.mp4"},
}.items():
    check(f"acha a URL em {shape}", find_video_url(job) == "https://cdn/a.mp4", str(job))
check("sem URL devolve None", find_video_url({"status": "completed"}) is None)

# ------------------------------------------------- ciclo completo (falso)
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64


def handler(request: httpx.Request) -> httpx.Response:
    calls.append(request)
    if request.method == "POST":
        return httpx.Response(200, json={"request_id": "req_9", "status": "queued"})
    if request.url.host == "cdn.example":
        return httpx.Response(200, content=MP4, headers={"content-type": "video/mp4"})
    polls = sum(1 for c in calls if c.url.path.endswith("/status"))
    if polls < 2:
        return httpx.Response(200, json={"request_id": "req_9", "status": "in_progress"})
    return httpx.Response(200, json={"request_id": "req_9", "status": "completed", "video": {"url": "https://cdn.example/v.mp4"}})


original_client = httpx.Client
httpx.Client = lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs)
hf_module.POLL_INTERVAL_SECONDS = 0

result = kling.generate(VideoRequest(prompt="A little chipmunk", mode="image_to_video", duration_seconds=8,
                                      media=[MediaInput("image", b"\x89PNG", "image/png", "first_frame")]))
check("devolve o mp4 baixado", result.data == MP4 and result.mime_type == "video/mp4")
check("guarda o request_id", result.interaction_id == "req_9", str(result.interaction_id))
check("POST foi para image-to-video", calls[0].url.path.endswith("/pro/image-to-video"), calls[0].url.path)
check("POST leva o Authorization", calls[0].headers["authorization"] == "Key kid:ksecret")
check("consultou /requests/{id}/status até concluir", sum(1 for c in calls if c.url.path == "/requests/req_9/status") >= 2)
download = next(c for c in calls if c.url.host == "cdn.example")
check("download da URL assinada não leva a chave", "authorization" not in download.headers)


def failing(request: httpx.Request) -> httpx.Response:
    if request.method == "POST":
        return httpx.Response(200, json={"request_id": "req_x", "status": "queued"})
    return httpx.Response(200, json={"status": "nsfw"})


httpx.Client = lambda **kwargs: original_client(transport=httpx.MockTransport(failing), **kwargs)
try:
    kling.generate(VideoRequest(prompt="x", mode="text_to_video"))
    check("status nsfw vira ProviderError", False, "não levantou")
except ProviderError as exc:
    check("status nsfw vira ProviderError", "nsfw" in str(exc), str(exc))
httpx.Client = lambda **kwargs: original_client(transport=httpx.MockTransport(lambda r: httpx.Response(401, text="no")), **kwargs)
try:
    kling.generate(VideoRequest(prompt="x", mode="text_to_video"))
    check("HTTP 401 vira ProviderError", False, "não levantou")
except ProviderError as exc:
    check("HTTP 401 vira ProviderError", "401" in str(exc), str(exc))
httpx.Client = original_client

# ------------------------------------------------------------------ config
s = config.get_settings()
check("auto escolhe higgsfield quando só ele tem credencial",
      config.Settings(**{**s.__dict__, "api_key": "", "azure_endpoint": "", "azure_api_key": "",
                         "higgsfield_key_id": "a", "higgsfield_key_secret": "b", "provider": "auto"}).effective_provider == "higgsfield")
check("Gemini continua à frente no auto",
      config.Settings(**{**s.__dict__, "api_key": "g", "higgsfield_key_id": "a", "higgsfield_key_secret": "b", "provider": "auto"}).effective_provider == "gemini")

print(f"\n{'TUDO OK' if not failures else str(len(failures)) + ' FALHA(S)'}")
raise SystemExit(1 if failures else 0)

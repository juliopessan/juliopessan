"""Provider Higgsfield: Kling 3.0 e Wan 3.0 pela API REST.

Auth: `Authorization: Key KEY_ID:KEY_SECRET` contra `https://api.higgsfield.ai`
(chave criada em console.higgsfield.ai). O ciclo é o da fila do Higgsfield: um
POST no caminho do modelo devolve `request_id`; `GET /requests/{id}/status` é
consultado até o fim; o MP4 vem por URL no resultado.

O que foi confirmado e o que não foi (o sandbox de desenvolvimento não alcança
`higgsfield.ai`, então nada aqui rodou contra a API real):
- confirmado em fontes públicas: base URL, formato do `Authorization`, o endpoint
  de status e o caminho do Kling (`kling-video/v3.0/{std|pro|4k}/text-to-video`);
- inferido: o sufixo `image-to-video`, o caminho do Wan 3.0, os nomes dos campos do
  corpo e o formato do resultado. Por isso o caminho é sobrescrevível
  (`VF_HIGGSFIELD_PATH`) e a extração da URL do vídeo aceita as formas comuns.

Capacidades: não estende cena (a continuidade sai do último frame, como no Sora-2);
Kling aceita 3–15 s, Wan 3.0 aceita 2–30 s.
"""
from __future__ import annotations

import base64
import os
import time
from typing import Any

from .base import ProviderError, VideoRequest, VideoResult

BASE_URL = "https://api.higgsfield.ai"
POLL_INTERVAL_SECONDS = 5
POLL_TIMEOUT_SECONDS = 1800

KLING = "kling-3.0"
WAN = "wan-3.0"
KLING_TIERS = ("std", "pro", "4k")

# Faixa de duração por modelo (ficha dos modelos no catálogo do Higgsfield).
SECONDS_RANGE = {KLING: (3, 15), WAN: (2, 30)}
ASPECT_RATIOS = ("16:9", "9:16", "1:1")

# Caminho de texto→vídeo. Kling confirmado em fontes públicas; Wan inferido.
TEXT_PATHS = {
    KLING: "kling-video/v3.0/{tier}/text-to-video",
    WAN: "wan/v3.0/text-to-video",
}

DONE = {"completed", "succeeded", "success"}
FAILED = {"failed", "nsfw", "canceled", "cancelled", "error"}


def clamp_seconds(model: str, seconds: int) -> int:
    low, high = SECONDS_RANGE[model]
    return max(low, min(high, int(seconds)))


def find_video_url(job: dict[str, Any]) -> str | None:
    """Acha a URL do MP4 nas formas de resultado que a fila costuma devolver."""
    video = job.get("video")
    if isinstance(video, dict) and video.get("url"):
        return video["url"]
    for key in ("videos", "results", "outputs"):
        items = job.get(key)
        if isinstance(items, list) and items:
            first = items[0]
            if isinstance(first, dict):
                nested = first.get("url") or (first.get("video") or {}).get("url") or (first.get("raw") or {}).get("url")
                if nested:
                    return nested
            elif isinstance(first, str):
                return first
    for key in ("output", "result"):
        nested = job.get(key)
        if isinstance(nested, dict):
            found = find_video_url(nested)
            if found:
                return found
        elif isinstance(nested, str) and nested.startswith("http"):
            return nested
    if isinstance(job.get("url"), str):
        return job["url"]
    return None


class HiggsfieldProvider:
    name = "higgsfield"

    def __init__(
        self,
        key_id: str | None = None,
        key_secret: str | None = None,
        model: str | None = None,
        tier: str | None = None,
        path: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.key_id = (key_id or os.environ.get("HIGGSFIELD_KEY_ID", "")).strip()
        self.key_secret = (key_secret or os.environ.get("HIGGSFIELD_KEY_SECRET", "")).strip()
        self.model = (model or os.environ.get("VF_HIGGSFIELD_MODEL") or KLING).strip().lower()
        self.tier = (tier or os.environ.get("VF_HIGGSFIELD_TIER") or "std").strip().lower()
        self.path = (path or os.environ.get("VF_HIGGSFIELD_PATH") or "").strip().strip("/")
        self.base_url = (base_url or os.environ.get("VF_HIGGSFIELD_BASE_URL") or BASE_URL).rstrip("/")
        if not self.key_id or not self.key_secret:
            raise ProviderError(
                "Configure HIGGSFIELD_KEY_ID e HIGGSFIELD_KEY_SECRET (console.higgsfield.ai) "
                "para usar Kling 3.0 ou Wan 3.0."
            )
        if self.model not in TEXT_PATHS:
            raise ProviderError(f"Modelo Higgsfield desconhecido: {self.model}. Use {', '.join(TEXT_PATHS)}.")
        if self.model == KLING and self.tier not in KLING_TIERS:
            raise ProviderError(f"Tier do Kling inválido: {self.tier}. Use {', '.join(KLING_TIERS)}.")

    # -- capacidades -----------------------------------------------------------

    @staticmethod
    def capabilities() -> dict[str, Any]:
        return {
            "extend": False,           # sem previous_interaction_id: encadeia por keyframe
            "reference_video": False,
            "upscale": False,
            "resolutions": ["480p", "720p", "1080p", "4k"],
            "aspect_ratios": list(ASPECT_RATIOS),
            "durations": [],           # faixa contínua (3–15 s Kling, 2–30 s Wan)
        }

    # -- montagem da requisicao ------------------------------------------------

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Key {self.key_id}:{self.key_secret}", "Content-Type": "application/json"}

    def endpoint(self, image: bool = False) -> str:
        path = self.path or TEXT_PATHS[self.model].format(tier=self.tier)
        if image:
            path = path.replace("text-to-video", "image-to-video")
        return f"{self.base_url}/{path}"

    @staticmethod
    def _data_uri(media) -> str:
        return f"data:{media.mime_type or 'image/png'};base64,{base64.b64encode(media.data).decode()}"

    def build_payload(self, request: VideoRequest) -> dict[str, Any]:
        if request.aspect_ratio not in ASPECT_RATIOS:
            raise ProviderError(
                f"{self.model} aceita {', '.join(ASPECT_RATIOS)}; recebeu {request.aspect_ratio}."
            )
        payload: dict[str, Any] = {
            "prompt": request.prompt.strip(),
            "duration": clamp_seconds(self.model, request.duration_seconds),
            "aspect_ratio": request.aspect_ratio,
        }
        if self.model == WAN:
            payload["resolution"] = request.resolution if request.resolution in ("480p", "720p", "1080p") else "720p"
        if request.seed is not None:
            payload["seed"] = request.seed
        images = [m for m in request.media if m.kind == "image"]
        first = next((m for m in images if m.role in ("first_frame", "reference")), None)
        last = next((m for m in images if m.role == "last_frame"), None)
        if first:
            payload["image_url"] = self._data_uri(first)
        if last:
            payload["end_image_url"] = self._data_uri(last)
        return payload

    # -- execucao --------------------------------------------------------------

    def generate(self, request: VideoRequest) -> VideoResult:
        import httpx

        if request.mode == "extend":
            raise ProviderError(
                "Kling e Wan não estendem cena a partir de outra geração. Use o encadeamento por "
                "keyframe (o pipeline faz isso sozinho) ou o provider gemini."
            )
        payload = self.build_payload(request)
        with httpx.Client(timeout=120, follow_redirects=True) as client:
            job = self._json(
                client.post(self.endpoint(image="image_url" in payload), headers=self.headers, json=payload),
                "criar o vídeo",
            )
            request_id = job.get("request_id") or job.get("id")
            if not request_id:
                raise ProviderError(f"Resposta sem request_id: {str(job)[:200]}")
            job = self._await_completion(client, request_id, job)
            url = find_video_url(job)
            if not url:
                raise ProviderError(f"Job concluído sem URL de vídeo: {str(job)[:200]}")
            download = client.get(url)  # URL assinada: sem o cabeçalho de auth
            if download.status_code >= 400:
                raise ProviderError(f"Falha ao baixar o vídeo: HTTP {download.status_code}")
            return VideoResult(
                interaction_id=request_id,
                data=download.content,
                mime_type=download.headers.get("content-type", "video/mp4").split(";")[0],
                raw_status=str(job.get("status", "completed")),
            )

    def _await_completion(self, client, request_id: str, job: dict) -> dict:
        deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
        while str(job.get("status", "")).lower() not in DONE:
            status = str(job.get("status", "")).lower()
            if status in FAILED:
                detail = job.get("error") or job.get("message") or ""
                raise ProviderError(f"{self.model} terminou com status '{status}'. {detail}")
            if time.monotonic() > deadline:
                raise ProviderError(f"Tempo esgotado ({POLL_TIMEOUT_SECONDS}s) aguardando o Higgsfield.")
            time.sleep(POLL_INTERVAL_SECONDS)
            job = self._json(
                client.get(f"{self.base_url}/requests/{request_id}/status", headers=self.headers),
                "consultar o job",
            )
        return job

    @staticmethod
    def _json(response, action: str) -> dict:
        if response.status_code >= 400:
            raise ProviderError(f"Falha ao {action}: HTTP {response.status_code} — {response.text[:300]}")
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError(f"Resposta não-JSON ao {action}: {response.text[:200]}") from exc

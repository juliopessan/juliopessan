"""
Publica o snapshot operacional em um arquivo JSON no Google Drive.

O Drive é só o carteiro: o bot escreve, o Órbita OS lê pelo conector do Google
Drive do próprio dono. Nenhuma porta é aberta no servidor do bot.

Configuração (.env):
    GOOGLE_SERVICE_ACCOUNT_FILE=/caminho/service-account.json
    ORBITA_DRIVE_FILE_ID=<id do orbita-whatsapp.json>
    ORBITA_PUBLISH_SECONDS=120

O arquivo precisa estar compartilhado como Editor com o e-mail da conta de
serviço. Sem as duas variáveis, o publicador fica desligado e o bot roda normal.
"""
import asyncio
import io
import json
import logging
import os

log = logging.getLogger("whatsapp-chatbot.drive")

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
DRIVE_FILE_ID = os.getenv("ORBITA_DRIVE_FILE_ID", "")
PUBLISH_SECONDS = max(30, int(os.getenv("ORBITA_PUBLISH_SECONDS", "120")))
SCOPES = ["https://www.googleapis.com/auth/drive"]

_service = None


def is_configured() -> bool:
    return bool(SERVICE_ACCOUNT_FILE and DRIVE_FILE_ID and os.path.exists(SERVICE_ACCOUNT_FILE))


def _client():
    global _service
    if _service is None:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        _service = build("drive", "v3", credentials=creds, cache_discovery=False)
    return _service


def publish_sync(snapshot: dict) -> None:
    """Sobrescreve o conteúdo do arquivo. Bloqueante — chamar via asyncio.to_thread."""
    from googleapiclient.http import MediaIoBaseUpload
    body = json.dumps(snapshot, ensure_ascii=False, indent=2).encode("utf-8")
    media = MediaIoBaseUpload(io.BytesIO(body), mimetype="application/json", resumable=False)
    _client().files().update(fileId=DRIVE_FILE_ID, media_body=media).execute()


async def publish(snapshot: dict) -> bool:
    if not is_configured():
        return False
    try:
        await asyncio.to_thread(publish_sync, snapshot)
        return True
    except Exception as exc:                                   # publicação nunca derruba o bot
        log.warning("Falha ao publicar status no Drive: %s", exc)
        return False


async def publisher_loop(snapshot_fn) -> None:
    """Publica a cada PUBLISH_SECONDS até ser cancelado."""
    log.info("Publicador do Drive ativo — a cada %ss no arquivo %s", PUBLISH_SECONDS, DRIVE_FILE_ID)
    while True:
        try:
            await publish(snapshot_fn())
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.warning("Ciclo do publicador falhou: %s", exc)
        await asyncio.sleep(PUBLISH_SECONDS)

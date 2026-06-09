import httpx
from config.settings import WHATSAPP_TOKEN

GRAPH_API_URL = "https://graph.facebook.com/v20.0"


async def send_message(phone_number_id: str, to: str, text: str) -> dict:
    url = f"{GRAPH_API_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


def extract_message(payload: dict) -> tuple[str | None, str | None, str | None]:
    """
    Returns (phone_number_id, customer_phone, message_text) from webhook payload.
    Returns None values if the payload has no processable message.
    """
    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]
        value = change["value"]

        phone_number_id = value["metadata"]["phone_number_id"]
        messages = value.get("messages", [])

        if not messages:
            return None, None, None

        msg = messages[0]
        if msg.get("type") != "text":
            return phone_number_id, msg["from"], None

        return phone_number_id, msg["from"], msg["text"]["body"]
    except (KeyError, IndexError):
        return None, None, None

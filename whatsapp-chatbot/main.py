import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse

from config.settings import WHATSAPP_VERIFY_TOKEN, HOST, PORT, load_company_by_phone
from integrations.whatsapp import extract_message, send_message
from bot.chatbot import generate_reply, get_greeting

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/chatbot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("whatsapp-chatbot")

GREETED: set[str] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("WhatsApp Chatbot iniciado. Aguardando mensagens...")
    yield
    log.info("Servidor encerrado.")


app = FastAPI(title="WhatsApp Chatbot", version="1.0.0", lifespan=lifespan)


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        log.info("Webhook verificado com sucesso.")
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Token de verificação inválido.")


@app.post("/webhook")
async def receive_message(request: Request):
    payload = await request.json()
    log.debug("Payload recebido: %s", payload)

    phone_number_id, customer_phone, message_text = extract_message(payload)

    if not phone_number_id:
        return {"status": "ignored"}

    company = load_company_by_phone(phone_number_id)
    if not company:
        log.warning("Empresa não encontrada para phone_number_id=%s", phone_number_id)
        return {"status": "company_not_found"}

    company_id = company.get("company_id")
    log.info("[%s] Mensagem de %s: %s", company_id, customer_phone, message_text)

    greeting_key = f"{company_id}:{customer_phone}"
    if greeting_key not in GREETED:
        GREETED.add(greeting_key)
        if not message_text:
            greeting = get_greeting(company)
            await send_message(phone_number_id, customer_phone, greeting)
            return {"status": "greeting_sent"}

    if not message_text:
        await send_message(
            phone_number_id,
            customer_phone,
            "Recebi sua mensagem! No momento só consigo processar texto. Por favor, envie uma mensagem escrita. 😊",
        )
        return {"status": "non_text_handled"}

    reply, needs_handoff = generate_reply(company, customer_phone, message_text)
    await send_message(phone_number_id, customer_phone, reply)

    if needs_handoff:
        log.info("[%s] Transferência humana solicitada por %s", company_id, customer_phone)
        escalation = company.get("escalation", {})
        if escalation.get("enabled"):
            notify_msg = escalation.get("notify_message", "").replace(
                "{customer_phone}", customer_phone
            )
            log.info("ESCALATION: %s → %s", escalation.get("notify_email"), notify_msg)

    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "online", "service": "WhatsApp Chatbot"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)

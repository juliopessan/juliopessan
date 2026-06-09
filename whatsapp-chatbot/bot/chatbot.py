import re
from datetime import datetime
from zoneinfo import ZoneInfo
from anthropic import Anthropic
from config.settings import ANTHROPIC_API_KEY

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# In-memory conversation history keyed by (company_id, customer_phone)
_conversations: dict[str, list[dict]] = {}
_MAX_HISTORY = 20


def _conversation_key(company_id: str, phone: str) -> str:
    return f"{company_id}:{phone}"


def _get_history(company_id: str, phone: str) -> list[dict]:
    key = _conversation_key(company_id, phone)
    return _conversations.setdefault(key, [])


def _append_history(company_id: str, phone: str, role: str, content: str) -> None:
    history = _get_history(company_id, phone)
    history.append({"role": role, "content": content})
    if len(history) > _MAX_HISTORY:
        history.pop(0)


def _is_open(company: dict) -> bool:
    tz_name = "America/Sao_Paulo"
    now = datetime.now(ZoneInfo(tz_name))
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    day_key = day_names[now.weekday()]
    hours = company.get("hours", {}).get(day_key)
    if not hours:
        return False
    open_h, open_m = map(int, hours["open"].split(":"))
    close_h, close_m = map(int, hours["close"].split(":"))
    open_time = now.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
    close_time = now.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
    return open_time <= now <= close_time


def _format_business_hours(company: dict) -> str:
    day_labels = {
        "monday": "Segunda", "tuesday": "Terça", "wednesday": "Quarta",
        "thursday": "Quinta", "friday": "Sexta", "saturday": "Sábado", "sunday": "Domingo"
    }
    lines = []
    for day, label in day_labels.items():
        hours = company.get("hours", {}).get(day)
        if hours:
            lines.append(f"• {label}: {hours['open']} às {hours['close']}")
        else:
            lines.append(f"• {label}: Fechado")
    return "\n".join(lines)


def _check_human_handoff(message: str, company: dict) -> bool:
    keywords = company.get("ai", {}).get("human_handoff_keywords", [])
    msg_lower = message.lower()
    return any(kw.lower() in msg_lower for kw in keywords)


def _build_system_prompt(company: dict) -> str:
    identity = company.get("identity", {})
    business = company.get("business", {})
    faq = company.get("faq", [])
    extra = company.get("ai", {}).get("system_prompt_extra", "")

    faq_text = "\n".join(
        f"P: {item['question']}\nR: {item['answer']}" for item in faq
    ) if faq else "Nenhuma FAQ configurada."

    hours_text = _format_business_hours(company)
    open_now = _is_open(company)

    return f"""Você é {identity.get('assistant_name', 'Assistente')}, assistente virtual da empresa *{company.get('name')}*.

INFORMAÇÕES DA EMPRESA:
- Segmento: {business.get('segment', 'N/A')}
- Descrição: {business.get('description', 'N/A')}
- Site: {business.get('website', 'N/A')}
- Email: {business.get('email', 'N/A')}
- Telefone: {business.get('phone', 'N/A')}
- Endereço: {business.get('address', 'N/A')}

HORÁRIO DE FUNCIONAMENTO:
{hours_text}
Status atual: {'Aberto' if open_now else 'Fechado'}

PERGUNTAS FREQUENTES (FAQ):
{faq_text}

INSTRUÇÕES DE COMPORTAMENTO:
- Tom: {identity.get('tone', 'profissional')}
- Idioma: {identity.get('language', 'pt-BR')}
- Seja conciso e objetivo — respostas curtas funcionam melhor no WhatsApp
- Use *negrito* para destacar informações importantes
- Use emojis com moderação para tornar a conversa mais amigável
- Se não souber a resposta, diga honestamente e ofereça alternativas
- Nunca invente informações sobre produtos, preços ou políticas
- Se o cliente pedir para falar com humano, responda com: [TRANSFERIR_HUMANO]

{extra}"""


def generate_reply(company: dict, customer_phone: str, message: str) -> tuple[str, bool]:
    """
    Returns (reply_text, needs_human_handoff).
    """
    company_id = company.get("company_id", "default")
    quick_replies = company.get("quick_replies", {})

    if _check_human_handoff(message, company):
        template = quick_replies.get("human_handoff", "Transferindo para atendente...")
        return template, True

    if not _is_open(company):
        hours_text = _format_business_hours(company)
        template = quick_replies.get(
            "out_of_hours",
            "Estamos fora do horário de atendimento.\n{business_hours}"
        )
        reply = template.replace("{business_hours}", hours_text)
        reply = reply.replace("{assistant_name}", company.get("identity", {}).get("assistant_name", "Assistente"))
        reply = reply.replace("{company_name}", company.get("name", ""))
        return reply, False

    _append_history(company_id, customer_phone, "user", message)
    history = _get_history(company_id, customer_phone)

    ai_config = company.get("ai", {})
    response = client.messages.create(
        model=ai_config.get("model", "claude-sonnet-4-6"),
        max_tokens=ai_config.get("max_tokens", 500),
        system=_build_system_prompt(company),
        messages=history,
    )

    reply = response.content[0].text.strip()

    if "[TRANSFERIR_HUMANO]" in reply:
        reply = reply.replace("[TRANSFERIR_HUMANO]", "").strip()
        template = quick_replies.get("human_handoff", "Transferindo para atendente...")
        _append_history(company_id, customer_phone, "assistant", template)
        return template, True

    _append_history(company_id, customer_phone, "assistant", reply)
    return reply, False


def clear_history(company_id: str, phone: str) -> None:
    key = _conversation_key(company_id, phone)
    _conversations.pop(key, None)


def get_greeting(company: dict) -> str:
    identity = company.get("identity", {})
    quick_replies = company.get("quick_replies", {})
    template = quick_replies.get(
        "greeting",
        "Olá! Sou {assistant_name} da {company_name}. Como posso ajudar?"
    )
    return (
        template
        .replace("{assistant_name}", identity.get("assistant_name", "Assistente"))
        .replace("{company_name}", company.get("name", ""))
    )

import copy
from pathlib import Path
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from admin.auth import verify_session, check_password, create_session_token, COOKIE_NAME
from config.settings import load_company, list_companies, save_company, COMPANIES_DIR

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Jinja2 helper: enumerate filter
templates.env.filters["enumerate"] = enumerate

COMPANY_TEMPLATE = {
    "company_id": "",
    "name": "",
    "whatsapp_phone_number_id": "",
    "active": True,
    "identity": {"assistant_name": "Sofia", "language": "pt-BR", "tone": "profissional e amigável"},
    "business": {"segment": "", "description": "", "website": "", "email": "", "phone": "", "address": ""},
    "hours": {
        "monday":    {"open": "09:00", "close": "18:00"},
        "tuesday":   {"open": "09:00", "close": "18:00"},
        "wednesday": {"open": "09:00", "close": "18:00"},
        "thursday":  {"open": "09:00", "close": "18:00"},
        "friday":    {"open": "09:00", "close": "18:00"},
        "saturday":  None,
        "sunday":    None,
    },
    "ai": {
        "model": "claude-sonnet-4-6",
        "max_tokens": 500,
        "temperature": 0.7,
        "system_prompt_extra": "",
        "human_handoff_keywords": ["falar com atendente", "falar com humano", "atendente"],
    },
    "faq": [],
    "quick_replies": {
        "greeting": "Olá! Sou *{assistant_name}* da *{company_name}*. Como posso te ajudar hoje?",
        "out_of_hours": "Estamos fora do horário! Nosso horário:\n{business_hours}\n\nDeixe sua mensagem! 😊",
        "human_handoff": "Transferindo para atendente. Aguarde! ⏳",
        "farewell": "Foi um prazer! Qualquer dúvida, é só chamar. 😊",
    },
    "escalation": {"enabled": False, "notify_email": "", "notify_message": "Atendimento solicitado por {customer_phone}"},
}


def _redirect(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=302)


def _guard(request: Request):
    if not verify_session(request):
        return _redirect("/admin/login")
    return None


# ── Auth ─────────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if verify_session(request):
        return _redirect("/admin")
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_submit(request: Request, password: str = Form(...)):
    if check_password(password):
        resp = _redirect("/admin")
        resp.set_cookie(COOKIE_NAME, create_session_token(), httponly=True, samesite="lax")
        return resp
    return templates.TemplateResponse("login.html", {"request": request, "error": "Senha incorreta."})


@router.get("/logout")
async def logout():
    resp = _redirect("/admin/login")
    resp.delete_cookie(COOKIE_NAME)
    return resp


# ── Dashboard ────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    if r := _guard(request):
        return r
    companies = [load_company(c["id"]) for c in list_companies()]
    active = sum(1 for c in companies if c and c.get("active"))
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active_page": "dashboard",
        "companies": companies,
        "total": len(companies),
        "active": active,
        "inactive": len(companies) - active,
    })


# ── Companies list ───────────────────────────────────────────────────────────

@router.get("/companies", response_class=HTMLResponse)
async def companies_list(request: Request):
    if r := _guard(request):
        return r
    companies = [load_company(c["id"]) for c in list_companies()]
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active_page": "companies",
        "companies": companies,
        "total": len(companies),
        "active": sum(1 for c in companies if c and c.get("active")),
        "inactive": sum(1 for c in companies if c and not c.get("active")),
    })


# ── New company ──────────────────────────────────────────────────────────────

@router.get("/companies/new", response_class=HTMLResponse)
async def company_new_page(request: Request):
    if r := _guard(request):
        return r
    return templates.TemplateResponse("company_form.html", {"request": request, "active_page": "new", "company": None})


@router.post("/companies/new")
async def company_new_submit(
    request: Request,
    company_id: str = Form(...),
    name: str = Form(...),
    phone_number_id: str = Form(...),
    assistant_name: str = Form("Sofia"),
    tone: str = Form("profissional e amigável"),
    segment: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    website: str = Form(""),
    address: str = Form(""),
    description: str = Form(""),
    notify_email: str = Form(""),
    escalation_enabled: str = Form(None),
):
    if r := _guard(request):
        return r
    if load_company(company_id):
        return templates.TemplateResponse("company_form.html", {
            "request": request, "active_page": "new", "company": None,
            "error": f"Empresa com ID '{company_id}' já existe.",
        })
    company = copy.deepcopy(COMPANY_TEMPLATE)
    company.update({
        "company_id": company_id,
        "name": name,
        "whatsapp_phone_number_id": phone_number_id,
    })
    company["identity"].update({"assistant_name": assistant_name, "tone": tone})
    company["business"].update({"segment": segment, "email": email, "phone": phone, "website": website, "address": address, "description": description})
    company["escalation"].update({"notify_email": notify_email, "enabled": escalation_enabled == "on"})
    save_company(company_id, company)
    return _redirect(f"/admin/companies/{company_id}?success=Empresa+criada+com+sucesso")


# ── Edit company (geral) ─────────────────────────────────────────────────────

@router.get("/companies/{company_id}", response_class=HTMLResponse)
async def company_edit_page(request: Request, company_id: str):
    if r := _guard(request):
        return r
    company = load_company(company_id)
    if not company:
        return _redirect("/admin/companies")
    ctx = {"request": request, "active_page": "companies", "company": company}
    if s := request.query_params.get("success"):
        ctx["success"] = s
    return templates.TemplateResponse("company_form.html", ctx)


@router.post("/companies/{company_id}")
async def company_edit_submit(
    request: Request,
    company_id: str,
    name: str = Form(...),
    phone_number_id: str = Form(...),
    assistant_name: str = Form("Sofia"),
    tone: str = Form("profissional e amigável"),
    segment: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    website: str = Form(""),
    address: str = Form(""),
    description: str = Form(""),
    notify_email: str = Form(""),
    escalation_enabled: str = Form(None),
):
    if r := _guard(request):
        return r
    company = load_company(company_id)
    if not company:
        return _redirect("/admin/companies")
    company.update({"name": name, "whatsapp_phone_number_id": phone_number_id})
    company["identity"].update({"assistant_name": assistant_name, "tone": tone})
    company["business"].update({"segment": segment, "email": email, "phone": phone, "website": website, "address": address, "description": description})
    company["escalation"].update({"notify_email": notify_email, "enabled": escalation_enabled == "on"})
    save_company(company_id, company)
    return _redirect(f"/admin/companies/{company_id}?success=Alterações+salvas")


# ── Toggle active ────────────────────────────────────────────────────────────

@router.post("/companies/{company_id}/toggle")
async def company_toggle(request: Request, company_id: str):
    if r := _guard(request):
        return r
    company = load_company(company_id)
    if company:
        company["active"] = not company["active"]
        save_company(company_id, company)
    return _redirect(f"/admin/companies/{company_id}?success=Status+atualizado")


# ── Delete company ───────────────────────────────────────────────────────────

@router.post("/companies/{company_id}/delete")
async def company_delete(request: Request, company_id: str):
    if r := _guard(request):
        return r
    path = COMPANIES_DIR / f"{company_id}.json"
    if path.exists():
        path.unlink()
    return _redirect("/admin/companies")


# ── Hours ────────────────────────────────────────────────────────────────────

@router.post("/companies/{company_id}/hours")
async def company_save_hours(request: Request, company_id: str):
    if r := _guard(request):
        return r
    company = load_company(company_id)
    if not company:
        return _redirect("/admin/companies")
    form = await request.form()
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for day in days:
        open_t = form.get(f"{day}_open", "").strip()
        close_t = form.get(f"{day}_close", "").strip()
        company["hours"][day] = {"open": open_t, "close": close_t} if open_t and close_t else None
    save_company(company_id, company)
    return _redirect(f"/admin/companies/{company_id}?success=Horários+salvos")


# ── FAQ ──────────────────────────────────────────────────────────────────────

@router.post("/companies/{company_id}/faq")
async def faq_add(request: Request, company_id: str, question: str = Form(...), answer: str = Form(...)):
    if r := _guard(request):
        return r
    company = load_company(company_id)
    if company:
        company["faq"].append({"question": question, "answer": answer})
        save_company(company_id, company)
    return _redirect(f"/admin/companies/{company_id}?success=Pergunta+adicionada")


@router.post("/companies/{company_id}/faq/{index}/delete")
async def faq_delete(request: Request, company_id: str, index: int):
    if r := _guard(request):
        return r
    company = load_company(company_id)
    if company and 0 <= index < len(company["faq"]):
        company["faq"].pop(index)
        save_company(company_id, company)
    return _redirect(f"/admin/companies/{company_id}?success=Pergunta+removida")


# ── AI settings ──────────────────────────────────────────────────────────────

@router.post("/companies/{company_id}/ai")
async def company_save_ai(
    request: Request,
    company_id: str,
    model: str = Form("claude-sonnet-4-6"),
    max_tokens: int = Form(500),
    handoff_keywords: str = Form(""),
    system_prompt_extra: str = Form(""),
):
    if r := _guard(request):
        return r
    company = load_company(company_id)
    if company:
        company["ai"].update({
            "model": model,
            "max_tokens": max_tokens,
            "system_prompt_extra": system_prompt_extra,
            "human_handoff_keywords": [k.strip() for k in handoff_keywords.split(",") if k.strip()],
        })
        save_company(company_id, company)
    return _redirect(f"/admin/companies/{company_id}?success=Configurações+de+IA+salvas")


# ── Messages ─────────────────────────────────────────────────────────────────

@router.post("/companies/{company_id}/messages")
async def company_save_messages(request: Request, company_id: str):
    if r := _guard(request):
        return r
    company = load_company(company_id)
    if company:
        form = await request.form()
        for key in ["greeting", "out_of_hours", "human_handoff", "farewell"]:
            val = form.get(key, "").strip()
            if val:
                company["quick_replies"][key] = val
        save_company(company_id, company)
    return _redirect(f"/admin/companies/{company_id}?success=Mensagens+salvas")

import json
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
COMPANIES_DIR = BASE_DIR / "config" / "companies"

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")


def load_company(company_id: str) -> Optional[dict]:
    path = COMPANIES_DIR / f"{company_id}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_company_by_phone(phone_number_id: str) -> Optional[dict]:
    for path in COMPANIES_DIR.glob("*.json"):
        with open(path, encoding="utf-8") as f:
            company = json.load(f)
        if company.get("whatsapp_phone_number_id") == phone_number_id and company.get("active"):
            return company
    return None


def list_companies() -> list[dict]:
    companies = []
    for path in COMPANIES_DIR.glob("*.json"):
        with open(path, encoding="utf-8") as f:
            company = json.load(f)
        companies.append({
            "id": company.get("company_id"),
            "name": company.get("name"),
            "active": company.get("active", False),
            "phone_number_id": company.get("whatsapp_phone_number_id"),
        })
    return companies


def save_company(company_id: str, data: dict) -> None:
    path = COMPANIES_DIR / f"{company_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

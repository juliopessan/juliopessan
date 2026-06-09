#!/usr/bin/env python3
"""
CLI para gerenciar configurações de empresas no WhatsApp Chatbot.

Uso:
    python admin/company_settings.py list
    python admin/company_settings.py show <company_id>
    python admin/company_settings.py create
    python admin/company_settings.py toggle <company_id>
    python admin/company_settings.py set-hours <company_id>
    python admin/company_settings.py add-faq <company_id>
    python admin/company_settings.py set-ai <company_id>
"""

import sys
import json
import copy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint

from config.settings import load_company, list_companies, save_company, COMPANIES_DIR

app = typer.Typer(help="Gerenciador de empresas — WhatsApp Chatbot")
console = Console()

COMPANY_TEMPLATE = {
    "company_id": "",
    "name": "",
    "whatsapp_phone_number_id": "",
    "active": True,
    "identity": {
        "assistant_name": "Assistente",
        "language": "pt-BR",
        "tone": "profissional e amigável",
    },
    "business": {
        "segment": "",
        "description": "",
        "website": "",
        "email": "",
        "phone": "",
        "address": "",
    },
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
        "greeting": "Olá! Sou *{assistant_name}* da *{company_name}*. Como posso te ajudar hoje?\n\n*1.* Horários\n*2.* Entrega\n*3.* Pagamentos\n*4.* Atendente",
        "out_of_hours": "Estamos fora do horário! Horários:\n{business_hours}\n\nDeixe sua mensagem! 😊",
        "human_handoff": "Transferindo para atendente. Aguarde! ⏳",
        "farewell": "Foi um prazer! Qualquer dúvida, é só chamar. 😊",
    },
    "escalation": {
        "enabled": False,
        "notify_email": "",
        "notify_message": "Solicitação de atendimento humano do número {customer_phone}",
    },
}


@app.command("list")
def cmd_list():
    """Lista todas as empresas cadastradas."""
    companies = list_companies()
    if not companies:
        rprint("[yellow]Nenhuma empresa cadastrada.[/yellow]")
        return

    table = Table(title="Empresas Cadastradas", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Nome", style="bold")
    table.add_column("Status")
    table.add_column("Phone Number ID")

    for c in companies:
        status = "[green]Ativa[/green]" if c["active"] else "[red]Inativa[/red]"
        table.add_row(c["id"], c["name"], status, c["phone_number_id"] or "—")

    console.print(table)


@app.command("show")
def cmd_show(company_id: str = typer.Argument(..., help="ID da empresa")):
    """Exibe configurações detalhadas de uma empresa."""
    company = load_company(company_id)
    if not company:
        rprint(f"[red]Empresa '{company_id}' não encontrada.[/red]")
        raise typer.Exit(1)

    console.print(Panel(
        json.dumps(company, ensure_ascii=False, indent=2),
        title=f"[bold]{company.get('name')}[/bold]",
        border_style="cyan",
    ))


@app.command("create")
def cmd_create():
    """Cria uma nova empresa interativamente."""
    rprint("[bold cyan]— Criar nova empresa —[/bold cyan]\n")

    company = copy.deepcopy(COMPANY_TEMPLATE)

    company_id = Prompt.ask("ID da empresa (sem espaços, ex: minha_loja)")
    if load_company(company_id):
        rprint(f"[red]Empresa '{company_id}' já existe.[/red]")
        raise typer.Exit(1)

    company["company_id"] = company_id
    company["name"] = Prompt.ask("Nome da empresa")
    company["whatsapp_phone_number_id"] = Prompt.ask("WhatsApp Phone Number ID (Meta)")
    company["identity"]["assistant_name"] = Prompt.ask("Nome do assistente virtual", default="Sofia")
    company["identity"]["tone"] = Prompt.ask("Tom de voz", default="profissional e amigável")
    company["business"]["segment"] = Prompt.ask("Segmento de negócio")
    company["business"]["description"] = Prompt.ask("Descrição da empresa")
    company["business"]["email"] = Prompt.ask("Email de contato")
    company["business"]["phone"] = Prompt.ask("Telefone (exibido no chat)")
    company["escalation"]["notify_email"] = Prompt.ask("Email para alertas de transferência humana")
    company["escalation"]["enabled"] = Confirm.ask("Ativar notificação por email?", default=False)

    save_company(company_id, company)
    rprint(f"\n[green]✓ Empresa '{company['name']}' criada com sucesso![/green]")
    rprint(f"[dim]Arquivo: config/companies/{company_id}.json[/dim]")
    rprint("[yellow]Próximos passos:[/yellow]")
    rprint("  • Edite o arquivo JSON para ajustar horários e FAQ")
    rprint(f"  • Use: [bold]python admin/company_settings.py add-faq {company_id}[/bold]")
    rprint(f"  • Use: [bold]python admin/company_settings.py set-hours {company_id}[/bold]")


@app.command("toggle")
def cmd_toggle(company_id: str = typer.Argument(..., help="ID da empresa")):
    """Ativa ou desativa uma empresa."""
    company = load_company(company_id)
    if not company:
        rprint(f"[red]Empresa '{company_id}' não encontrada.[/red]")
        raise typer.Exit(1)

    company["active"] = not company["active"]
    save_company(company_id, company)
    status = "ativada" if company["active"] else "desativada"
    rprint(f"[green]✓ Empresa '{company['name']}' {status}.[/green]")


@app.command("set-hours")
def cmd_set_hours(company_id: str = typer.Argument(..., help="ID da empresa")):
    """Configura os horários de funcionamento."""
    company = load_company(company_id)
    if not company:
        rprint(f"[red]Empresa '{company_id}' não encontrada.[/red]")
        raise typer.Exit(1)

    rprint(f"\n[bold cyan]Horários de funcionamento — {company['name']}[/bold cyan]")
    rprint("[dim]Deixe em branco para marcar como fechado.[/dim]\n")

    days = {
        "monday": "Segunda-feira",
        "tuesday": "Terça-feira",
        "wednesday": "Quarta-feira",
        "thursday": "Quinta-feira",
        "friday": "Sexta-feira",
        "saturday": "Sábado",
        "sunday": "Domingo",
    }

    for key, label in days.items():
        current = company["hours"].get(key)
        current_str = f"{current['open']} às {current['close']}" if current else "Fechado"
        rprint(f"[bold]{label}[/bold] (atual: {current_str})")

        open_t = Prompt.ask("  Abertura (HH:MM)", default=current["open"] if current else "")
        if not open_t:
            company["hours"][key] = None
            rprint("  → Fechado\n")
            continue

        close_t = Prompt.ask("  Fechamento (HH:MM)", default=current["close"] if current else "18:00")
        company["hours"][key] = {"open": open_t, "close": close_t}
        rprint(f"  → {open_t} às {close_t}\n")

    save_company(company_id, company)
    rprint("[green]✓ Horários salvos![/green]")


@app.command("add-faq")
def cmd_add_faq(company_id: str = typer.Argument(..., help="ID da empresa")):
    """Adiciona uma pergunta ao FAQ da empresa."""
    company = load_company(company_id)
    if not company:
        rprint(f"[red]Empresa '{company_id}' não encontrada.[/red]")
        raise typer.Exit(1)

    rprint(f"\n[bold cyan]FAQ — {company['name']}[/bold cyan]")

    if company["faq"]:
        rprint(f"\nFAQ atual: {len(company['faq'])} pergunta(s)\n")

    while True:
        question = Prompt.ask("\nPergunta (ou Enter para sair)")
        if not question:
            break
        answer = Prompt.ask("Resposta")
        company["faq"].append({"question": question, "answer": answer})
        rprint("[green]✓ Pergunta adicionada.[/green]")

    save_company(company_id, company)
    rprint(f"\n[green]✓ FAQ salvo com {len(company['faq'])} pergunta(s).[/green]")


@app.command("set-ai")
def cmd_set_ai(company_id: str = typer.Argument(..., help="ID da empresa")):
    """Configura parâmetros de IA da empresa."""
    company = load_company(company_id)
    if not company:
        rprint(f"[red]Empresa '{company_id}' não encontrada.[/red]")
        raise typer.Exit(1)

    rprint(f"\n[bold cyan]Configurações de IA — {company['name']}[/bold cyan]\n")

    ai = company.get("ai", {})

    models = ["claude-sonnet-4-6", "claude-opus-4-8", "claude-haiku-4-5-20251001"]
    rprint("Modelos disponíveis:")
    for i, m in enumerate(models, 1):
        rprint(f"  {i}. {m}")

    choice = Prompt.ask("Escolha o modelo", default="1")
    try:
        ai["model"] = models[int(choice) - 1]
    except (ValueError, IndexError):
        ai["model"] = models[0]

    ai["max_tokens"] = int(Prompt.ask("Máximo de tokens por resposta", default=str(ai.get("max_tokens", 500))))
    ai["system_prompt_extra"] = Prompt.ask(
        "Instruções adicionais para o assistente (Enter para manter)",
        default=ai.get("system_prompt_extra", ""),
    )

    keywords_str = Prompt.ask(
        "Palavras-chave para transferência humana (vírgula separados)",
        default=", ".join(ai.get("human_handoff_keywords", [])),
    )
    ai["human_handoff_keywords"] = [k.strip() for k in keywords_str.split(",") if k.strip()]

    company["ai"] = ai
    save_company(company_id, company)
    rprint("[green]✓ Configurações de IA salvas![/green]")


if __name__ == "__main__":
    app()

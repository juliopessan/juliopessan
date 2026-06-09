# WhatsApp Chatbot — Multi-Empresa com IA

Chatbot para WhatsApp Business com suporte a múltiplas empresas, configurações por empresa e respostas geradas por IA (Claude).

## Funcionalidades

- **Multi-empresa** — um servidor, múltiplos números WhatsApp Business
- **IA com contexto** — Claude responde com a personalidade e FAQ de cada empresa
- **Horários automáticos** — detecta se o negócio está aberto e adapta a resposta
- **Transferência humana** — detecta keywords e aciona escalação
- **Histórico de conversa** — mantém contexto dos últimos 20 turnos por cliente
- **CLI admin** — criar e gerenciar empresas pelo terminal

## Stack

| Camada | Tecnologia |
|---|---|
| Servidor | FastAPI + Uvicorn |
| IA | Anthropic Claude (claude-sonnet-4-6) |
| WhatsApp | Meta Cloud API (WhatsApp Business) |
| Config | JSON por empresa |
| Admin | CLI com Rich + Typer |

## Início rápido

```bash
# Instalar
pip install -r requirements.txt

# Configurar credenciais
cp .env.example .env   # preencher WHATSAPP_TOKEN, ANTHROPIC_API_KEY etc.

# Criar primeira empresa
python admin/company_settings.py create

# Iniciar servidor
python main.py
```

## CLI Admin

```bash
python admin/company_settings.py list            # listar empresas
python admin/company_settings.py create          # nova empresa
python admin/company_settings.py show <id>       # ver configurações
python admin/company_settings.py toggle <id>     # ativar/desativar
python admin/company_settings.py set-hours <id>  # configurar horários
python admin/company_settings.py add-faq <id>    # adicionar FAQ
python admin/company_settings.py set-ai <id>     # configurar modelo IA
```

## Estrutura

```
whatsapp-chatbot/
├── main.py                        # Webhook FastAPI
├── bot/chatbot.py                 # Lógica de IA + histórico
├── integrations/whatsapp.py       # Envio/recepção Meta API
├── config/settings.py             # Carregador multi-empresa
├── config/companies/*.json        # Perfil de cada empresa
└── admin/company_settings.py      # CLI de gerenciamento
```

Consulte o [SETUP.md](SETUP.md) para o guia completo de configuração do webhook na Meta.

# WhatsApp Chatbot SaaS — Multi-Empresa com IA

Plataforma SaaS para WhatsApp Business com painel web de administração, suporte a múltiplas empresas e respostas geradas por IA (Claude).

## Funcionalidades

- **Painel web admin** — gerenciar empresas pelo navegador, sem CLI
- **Multi-empresa** — um servidor, vários números WhatsApp Business
- **IA com contexto** — Claude responde com personalidade e FAQ de cada empresa
- **Horários automáticos** — detecta se o negócio está aberto e adapta a resposta
- **Transferência humana** — detecta keywords e aciona escalação
- **Histórico de conversa** — mantém contexto dos últimos 20 turnos por cliente

## Stack

| Camada | Tecnologia |
|---|---|
| Servidor | FastAPI + Uvicorn |
| Painel admin | Jinja2 templates (sem JS framework) |
| IA | Anthropic Claude (claude-sonnet-4-6) |
| WhatsApp | Meta Cloud API (WhatsApp Business) |
| Config | JSON por empresa |

## Início rápido

```bash
# Instalar
pip install -r requirements.txt

# Configurar credenciais
cp .env.example .env   # preencher tokens

# Iniciar servidor
python main.py
```

Acesse `http://localhost:8000/admin` e faça login com a senha definida em `ADMIN_PASSWORD`.

## Painel Admin

| Seção | O que faz |
|---|---|
| Dashboard | Visão geral das empresas cadastradas |
| Nova Empresa | Formulário completo de cadastro |
| Editar → Geral | Nome, assistente, dados do negócio |
| Editar → Horários | Horário de funcionamento por dia |
| Editar → FAQ | Perguntas frequentes injetadas na IA |
| Editar → IA | Modelo Claude, tokens, keywords de escalação |
| Editar → Mensagens | Textos automáticos personalizados |

## Variáveis de ambiente

```env
WHATSAPP_TOKEN=          # Token da Meta API
WHATSAPP_VERIFY_TOKEN=   # Token de verificação do webhook
ANTHROPIC_API_KEY=       # Chave da Anthropic
ADMIN_PASSWORD=          # Senha do painel web
SECRET_KEY=              # Chave para criptografia de sessão
PORT=8000
```

## Estrutura

```
whatsapp-chatbot/
├── main.py                        # FastAPI + webhook + admin
├── admin/
│   ├── panel.py                   # Rotas do painel web
│   ├── auth.py                    # Autenticação por sessão
│   └── templates/                 # HTML do painel
├── bot/chatbot.py                 # Lógica IA + histórico
├── integrations/whatsapp.py       # Meta Cloud API
├── config/
│   ├── settings.py                # Configurações globais
│   └── companies/*.json           # Perfil de cada empresa
└── logs/chatbot.log
```

Consulte o [SETUP.md](SETUP.md) para configurar o webhook na Meta.

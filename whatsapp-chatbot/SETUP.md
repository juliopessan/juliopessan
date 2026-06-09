# WhatsApp Chatbot — Guia de Setup

## Pré-requisitos

- Python 3.11+
- Conta no [Meta for Developers](https://developers.facebook.com/)
- Chave de API da [Anthropic](https://console.anthropic.com/)
- [ngrok](https://ngrok.com/) (para testes locais)

---

## 1. Instalação

```bash
cd whatsapp-chatbot
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

---

## 2. Variáveis de Ambiente

```bash
cp .env.example .env
```

Preencha o `.env`:

| Variável | Onde obter |
|---|---|
| `WHATSAPP_TOKEN` | Meta for Developers → App → WhatsApp → API Setup → Temporary Access Token |
| `WHATSAPP_VERIFY_TOKEN` | Qualquer string secreta que você escolher |
| `WHATSAPP_PHONE_NUMBER_ID` | Meta for Developers → App → WhatsApp → API Setup → Phone Number ID |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) |

---

## 3. Configurar a primeira empresa

```bash
python admin/company_settings.py create
```

O assistente vai pedir:
- ID da empresa (ex: `minha_loja`)
- Nome, segmento, descrição
- WhatsApp Phone Number ID
- Nome do assistente virtual

Depois adicione FAQ e horários:
```bash
python admin/company_settings.py set-hours minha_loja
python admin/company_settings.py add-faq minha_loja
```

---

## 4. Iniciar o servidor

```bash
python main.py
```

Para produção:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 5. Expor para a internet (desenvolvimento)

```bash
ngrok http 8000
```

Copie a URL HTTPS gerada (ex: `https://abc123.ngrok.io`).

---

## 6. Configurar Webhook no Meta

1. Acesse: Meta for Developers → seu App → WhatsApp → Configuration
2. Em **Webhook**, clique em **Edit**
3. **Callback URL:** `https://abc123.ngrok.io/webhook`
4. **Verify Token:** o mesmo que você colocou em `WHATSAPP_VERIFY_TOKEN`
5. Clique **Verify and Save**
6. Ative a assinatura para **messages**

---

## 7. Testar

Envie uma mensagem para o número WhatsApp Business e veja a resposta!

Logs em tempo real:
```bash
tail -f logs/chatbot.log
```

---

## Gerenciar empresas (CLI Admin)

```bash
# Listar todas as empresas
python admin/company_settings.py list

# Ver configurações de uma empresa
python admin/company_settings.py show minha_loja

# Ativar/desativar empresa
python admin/company_settings.py toggle minha_loja

# Configurar horários
python admin/company_settings.py set-hours minha_loja

# Adicionar FAQ
python admin/company_settings.py add-faq minha_loja

# Configurar IA (modelo, tokens, keywords)
python admin/company_settings.py set-ai minha_loja
```

---

## Adicionar uma segunda empresa

Basta repetir o `create` com um Phone Number ID diferente (um número WhatsApp por empresa):

```bash
python admin/company_settings.py create
```

O sistema detecta automaticamente qual empresa responder baseado no número de destino.

---

## Estrutura de arquivos

```
whatsapp-chatbot/
├── main.py                        # Servidor FastAPI + webhook
├── config/
│   ├── settings.py                # Carregador de configurações
│   └── companies/
│       └── minha_loja.json        # Configuração da empresa
├── bot/
│   └── chatbot.py                 # Lógica de IA + histórico de conversa
├── integrations/
│   └── whatsapp.py                # Envio/recepção de mensagens
├── admin/
│   └── company_settings.py        # CLI de gerenciamento
├── logs/
│   └── chatbot.log                # Logs de operação
└── .env                           # Credenciais (não commitar!)
```

---

## O que o chatbot faz automaticamente

- **Saudação inicial** ao primeiro contato
- **Verifica horário de funcionamento** antes de responder
- **Responde com IA** (Claude) usando FAQ e contexto da empresa
- **Detecta pedido de humano** e envia mensagem de transferência
- **Mantém histórico** de conversa por cliente (memória curta)
- **Multi-empresa:** cada número WhatsApp tem sua própria personalidade

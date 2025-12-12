# SaaS Contabil Converter

Bot do Telegram para conversão de PDFs contábeis para CSV.

## 🚀 Deploy para Produção

### Railway (Recomendado)

1. **Instalar Railway CLI:**
```bash
npm install -g @railway/cli
```

2. **Login e criar projeto:**
```bash
railway login
railway new
```

3. **Adicionar banco de dados:**
```bash
railway add postgresql
railway add redis
```

4. **Configurar variáveis de ambiente:**
```bash
railway variables set SECRET_KEY="sua-chave-secreta-32-chars"
railway variables set ADMIN_USERNAME="admin"
railway variables set ADMIN_PASSWORD="senha-segura"
railway variables set TELEGRAM_BOT_TOKEN="seu-token-real"
railway variables set TELEGRAM_WEBHOOK_SECRET="webhook-secreto"
railway variables set TELEGRAM_PROVIDER_TOKEN="provider-token"
railway variables set ENVIRONMENT="production"
```

5. **Deploy:**
```bash
railway up
```

## 🔧 Desenvolvimento Local

1. **Copiar variáveis de ambiente:**
```bash
cp .env.example .env
# Editar .env com suas configurações
```

2. **Iniciar serviços:**
```bash
docker-compose up postgres redis
```

3. **Iniciar aplicação:**
```bash
uvicorn src.api.main:app --reload
```

## 📋 Variáveis de Ambiente Necessárias

- `SECRET_KEY`: Chave secreta para JWT (32+ caracteres)
- `ADMIN_USERNAME`: Usuário admin da API
- `ADMIN_PASSWORD`: Senha admin da API
- `TELEGRAM_BOT_TOKEN`: Token do bot do Telegram
- `TELEGRAM_WEBHOOK_SECRET`: Secret para webhook
- `TELEGRAM_PROVIDER_TOKEN`: Token do provedor de pagamento
- `DATABASE_URL`: URL do PostgreSQL (auto no Railway)
- `REDIS_URL`: URL do Redis (auto no Railway)

## 🤖 Configurar Bot no Telegram

1. **Configurar comandos no BotFather:**
```
/setcommands
start - 🏠 Início - Informações e boas-vindas
help - ❓ Ajuda - Como usar o bot
preco - 💰 Preços - Valores e formas de pagamento
status - 📊 Status - Verificar suas conversões
```

2. **Configurar webhook:**
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://sua-url.railway.app/telegram/webhook" \
  -d "secret_token=seu-webhook-secret"
```
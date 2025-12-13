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

### Básicas
- `SECRET_KEY`: Chave secreta para JWT (32+ caracteres)
- `ADMIN_USERNAME`: Usuário admin da API
- `ADMIN_PASSWORD`: Senha admin da API
- `DATABASE_URL`: URL do PostgreSQL (auto no Railway)
- `REDIS_URL`: URL do Redis (auto no Railway)

### Telegram
- `TELEGRAM_BOT_TOKEN`: Token do bot do Telegram
- `TELEGRAM_WEBHOOK_SECRET`: Secret para webhook
- `TELEGRAM_PROVIDER_TOKEN`: Token do provedor de pagamento (opcional)

### Ammer Pay (Sistema de Pagamento)
- `AMMER_PAY_API_KEY`: Chave da API do Ammer Pay
- `AMMER_PAY_SECRET`: Secret para assinatura de webhooks
- `AMMER_PAY_WEBHOOK_SECRET`: Secret para validação de webhooks

### Configurações
- `MAX_FILE_SIZE`: Tamanho máximo do arquivo (padrão: 60MB)
- `ENVIRONMENT`: Ambiente (development/production)

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

## 💳 Integração Ammer Pay

O sistema agora usa Ammer Pay como provedor de pagamento principal.

### Configuração

1. **Obter credenciais do Ammer Pay:**
   - Registre-se no Ammer Pay
   - Obtenha API Key e Secret
   - Configure webhook URL: `https://sua-url.railway.app/ammer/webhook`

2. **Configurar variáveis:**
```bash
railway variables set AMMER_PAY_API_KEY="sua-api-key"
railway variables set AMMER_PAY_SECRET="seu-secret"
railway variables set AMMER_PAY_WEBHOOK_SECRET="webhook-secret"
```

3. **Executar migração do banco:**
```bash
python migration_ammer_pay.py
```

4. **Testar integração:**
```bash
python test_ammer_pay.py
```

### Fluxo de Pagamento

1. **Usuário envia PDF** → Sistema valida arquivo
2. **Sistema cria link de pagamento** → Ammer Pay gera URL
3. **Usuário clica no botão** → Redireciona para Ammer Pay
4. **Pagamento aprovado** → Webhook notifica sistema
5. **Conversão iniciada** → Arquivo processado automaticamente

## 📄 Regras de Negócio

### Arquivos
- **Formato aceito:** Apenas PDF
- **Tamanho máximo:** 60MB
- **Validação:** Apenas PDFs que começam com "Ponto"
- **Limite:** Um arquivo por usuário por vez

### Pagamento
- **Valor:** R$ 50,00 por conversão
- **Método:** Ammer Pay (PIX, cartão, etc.)
- **Processamento:** Automático após confirmação

### Controle de Fluxo
- **Um arquivo por vez:** Usuário deve aguardar processamento atual
- **Status em tempo real:** Comando /status mostra progresso
- **Notificações:** Bot informa sobre cada etapa

## 🧪 Testes

### Testar Bot Local
```bash
python verify_telegram.py
```

### Testar Ammer Pay
```bash
python test_ammer_pay.py
```

### Testar Segurança
```bash
python verify_security.py
```
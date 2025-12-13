# Changelog - Integração Ammer Pay

## 🚀 Novas Funcionalidades

### 💳 Sistema de Pagamento Ammer Pay
- **Substituição do Telegram Payments** por Ammer Pay
- **Botão de pagamento integrado** no chat do Telegram
- **Webhook para notificações** de pagamento em tempo real
- **Validação de assinatura** para segurança dos webhooks

### 📄 Controle de Arquivos Aprimorado
- **Limite aumentado para 60MB** (anteriormente 10MB)
- **Um arquivo por vez por usuário** - controle de fluxo
- **Validação de status** antes de aceitar novos arquivos
- **Mensagens informativas** sobre processamento em andamento

### 🔒 Melhorias de Segurança
- **Validação de valores** nos webhooks de pagamento
- **Verificação de assinatura** do Ammer Pay
- **Controle de estado** para evitar processamento duplicado

## 📋 Arquivos Modificados

### Configuração
- `src/core/config.py` - Adicionadas variáveis do Ammer Pay e limite de 60MB
- `.env.example` - Novas variáveis de ambiente

### Serviços
- `src/services/ammer_pay.py` - **NOVO** - Integração com Ammer Pay
- `src/services/telegram.py` - Adicionado método para teclado inline

### API e Modelos
- `src/api/telegram.py` - Fluxo completo com Ammer Pay e controle de arquivos
- `src/models/order.py` - Campos para Ammer Pay
- `src/api/main.py` - Limite de arquivo atualizado

### Scripts e Documentação
- `migration_ammer_pay.py` - **NOVO** - Migração do banco de dados
- `test_ammer_pay.py` - **NOVO** - Testes da integração
- `README.md` - Documentação atualizada
- `deploy.sh` - Instruções para Ammer Pay

## 🔄 Fluxo Atualizado

### Antes (Telegram Payments)
1. Usuário envia PDF
2. Sistema valida e cria fatura Telegram
3. Usuário paga via Telegram
4. Processamento iniciado

### Agora (Ammer Pay)
1. Usuário envia PDF
2. **Sistema verifica se há processamento pendente**
3. **Validação de arquivo até 60MB**
4. Sistema cria link de pagamento Ammer Pay
5. **Botão de pagamento no chat**
6. Usuário clica e paga via Ammer Pay
7. **Webhook notifica sistema automaticamente**
8. Processamento iniciado

## 🛠️ Configuração Necessária

### Variáveis de Ambiente
```bash
# Ammer Pay
AMMER_PAY_API_KEY=sua-api-key
AMMER_PAY_SECRET=seu-secret
AMMER_PAY_WEBHOOK_SECRET=webhook-secret

# Arquivo
MAX_FILE_SIZE=62914560  # 60MB
```

### Migração do Banco
```bash
python3 migration_ammer_pay.py
```

### Webhook do Ammer Pay
- URL: `https://sua-url.com/ammer/webhook`
- Eventos: `payment.completed`, `payment.failed`

## ✅ Benefícios

1. **Melhor UX**: Botão de pagamento direto no chat
2. **Mais opções**: PIX, cartão, boleto via Ammer Pay
3. **Controle de fluxo**: Um arquivo por vez evita confusão
4. **Arquivos maiores**: Suporte a PDFs de até 60MB
5. **Segurança**: Validação robusta de pagamentos
6. **Automação**: Webhook em tempo real

## 🧪 Como Testar

1. **Configurar credenciais** do Ammer Pay
2. **Executar migração** do banco de dados
3. **Testar integração** com script de teste
4. **Enviar PDF** via Telegram
5. **Verificar botão** de pagamento
6. **Simular pagamento** no Ammer Pay
7. **Confirmar processamento** automático
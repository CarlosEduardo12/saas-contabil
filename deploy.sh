#!/bin/bash

# Deploy script for SaaS Contabil Converter

echo "🚀 Iniciando deploy para produção..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "📋 Copie .env.example para .env e configure as variáveis"
    exit 1
fi

# Load environment variables
source .env

# Validate required variables
required_vars=("SECRET_KEY" "ADMIN_USERNAME" "ADMIN_PASSWORD" "TELEGRAM_BOT_TOKEN")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Variável $var não configurada!"
        exit 1
    fi
done

echo "✅ Variáveis de ambiente validadas"

# Build and start services
echo "🔨 Construindo containers..."
docker-compose -f docker-compose.prod.yml build

echo "🚀 Iniciando serviços..."
docker-compose -f docker-compose.prod.yml up -d

echo "⏳ Aguardando serviços iniciarem..."
sleep 10

# Check if services are running
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "✅ Serviços iniciados com sucesso!"
    echo "🌐 Aplicação disponível em: http://localhost:8000"
    echo "📊 Health check: http://localhost:8000/health"
else
    echo "❌ Erro ao iniciar serviços"
    docker-compose -f docker-compose.prod.yml logs
    exit 1
fi

echo "🎉 Deploy concluído!"

echo ""
echo "🔧 Próximos passos para Ammer Pay:"
echo "1. Configure as credenciais do Ammer Pay no .env"
echo "2. Execute a migração: python3 migration_ammer_pay.py"
echo "3. Teste a integração: python3 test_ammer_pay.py"
echo "4. Configure o webhook do Ammer Pay: http://localhost:8000/ammer/webhook"
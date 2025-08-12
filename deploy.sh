#!/bin/bash
# Script de deploy com migrações automáticas

echo "🚀 Iniciando deploy..."

# Para o serviço atual
echo "⏹️ Parando serviços..."
docker compose down

# Faz backup do banco (opcional)
echo "💾 Fazendo backup do banco..."
docker compose exec -T quiz_db pg_dump -U quiz_user quiz > backup_$(date +%Y%m%d_%H%M%S).sql 2>/dev/null || echo "Backup falhou (normal se banco não existir)"

# Reconstrói e inicia os serviços
echo "🔨 Reconstruindo aplicação..."
docker compose up --build -d

# Aguarda o banco estar pronto
echo "⏳ Aguardando banco de dados..."
sleep 10

# Aplica migrações
echo "🔄 Aplicando migrações..."
docker compose exec psicoquiz python migrate.py apply

echo "✅ Deploy concluído!"
echo "🌐 Aplicação disponível em: http://localhost:5000"
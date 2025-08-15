#!/bin/bash
# Script para sincronizar dados da produção

# Configurações (ajuste conforme necessário)
PROD_HOST="seu-servidor.com"
PROD_USER="usuario"
PROD_PATH="/path/to/psicoquiz"

echo "🌐 Sincronizando dados da produção..."

# Função para baixar via SSH
sync_ssh() {
    echo "📡 Método: SSH/SCP"
    python backup_restore.py sync $PROD_HOST $PROD_USER
}

# Função para baixar via Docker (se produção usar Docker)
sync_docker() {
    echo "🐳 Método: Docker remoto"
    
    # Criar backup na produção
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && docker-compose exec -T db pg_dump -U quiz_user -d quiz --no-owner --no-privileges" > prod_backup.sql
    
    if [ -f "prod_backup.sql" ]; then
        echo "✅ Backup baixado: prod_backup.sql"
        
        # Perguntar se quer restaurar
        read -p "🔄 Restaurar dados baixados? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python backup_restore.py restore prod_backup.sql
        fi
    else
        echo "❌ Falha no download"
    fi
}

# Função para baixar via API (se implementada)
sync_api() {
    echo "🌐 Método: API REST"
    
    # Exemplo de download via curl
    curl -H "Authorization: Bearer $API_TOKEN" \
         "$PROD_HOST/api/export" \
         -o prod_data.json
    
    if [ -f "prod_data.json" ]; then
        echo "✅ Dados baixados: prod_data.json"
        # Implementar importação via API local
    fi
}

# Menu de opções
echo "Escolha o método de sincronização:"
echo "1) SSH/SCP"
echo "2) Docker remoto"
echo "3) API REST"
read -p "Opção (1-3): " choice

case $choice in
    1) sync_ssh ;;
    2) sync_docker ;;
    3) sync_api ;;
    *) echo "❌ Opção inválida" ;;
esac
#!/usr/bin/env python3
"""
Script para restauração limpa de backup
"""
import os
import sys

def clean_restore(backup_file):
    """Restaura backup com limpeza completa do banco"""
    
    if not os.path.exists(backup_file):
        print(f"❌ Arquivo não encontrado: {backup_file}")
        return False
    
    print("🛑 Parando aplicação...")
    os.system("docker-compose down")
    
    print("🗑️ Removendo dados antigos...")
    os.system("docker volume rm comport_quiz_data 2>nul")
    
    print("🚀 Iniciando banco limpo...")
    os.system("docker-compose up -d db")
    
    print("⏳ Aguardando banco inicializar...")
    import time
    time.sleep(10)
    
    print(f"📥 Restaurando backup: {backup_file}")
    result = os.system(f'docker exec -i quiz_db psql -U quiz_user -d quiz < {backup_file}')
    
    if result == 0:
        print("✅ Backup restaurado com sucesso!")
        
        print("🚀 Iniciando aplicação completa...")
        os.system("docker-compose up -d")
        
        print("✅ Restauração concluída!")
        return True
    else:
        print("❌ Erro na restauração")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python clean_restore.py <arquivo_backup>")
        print("Exemplo: python clean_restore.py vps_backup_20250814_164257.sql")
        sys.exit(1)
    
    backup_file = sys.argv[1]
    clean_restore(backup_file)
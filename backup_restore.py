#!/usr/bin/env python3
"""
Sistema de Backup e Restore para PsicoQuiz
"""
import os
import json
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def backup_database():
    """Cria backup do PostgreSQL"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_psicoquiz_{timestamp}.sql"
    
    # Comando pg_dump
    cmd = [
        "docker", "exec", "quiz_db", 
        "pg_dump", "-U", "quiz_user", "-d", "quiz", 
        "--no-owner", "--no-privileges"
    ]
    
    try:
        print(f"📦 Criando backup: {backup_file}")
        with open(backup_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print(f"✅ Backup criado: {backup_file}")
            return backup_file
        else:
            print(f"❌ Erro no backup: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def export_json():
    """Exporta dados para JSON (compatível com versão antiga)"""
    from app import app
    from models import User
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = f"users_backup_{timestamp}.json"
    
    try:
        with app.app_context():
            users = User.query.all()
            users_data = {}
            
            for user in users:
                users_data[user.username] = user.to_dict()
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ JSON exportado: {json_file}")
            return json_file
    except Exception as e:
        print(f"❌ Erro ao exportar JSON: {e}")
        return None

def restore_database(backup_file):
    """Restaura backup do PostgreSQL"""
    if not os.path.exists(backup_file):
        print(f"❌ Arquivo não encontrado: {backup_file}")
        return False
    
    # Limpa banco atual
    cmd_drop = [
        "docker", "exec", "quiz_db",
        "psql", "-U", "quiz_user", "-d", "quiz",
        "-c", "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
    ]
    
    # Restaura backup
    cmd_restore = [
        "docker", "exec", "-i", "quiz_db",
        "psql", "-U", "quiz_user", "-d", "quiz"
    ]
    
    try:
        print("🗑️ Limpando banco atual...")
        subprocess.run(cmd_drop, check=True, capture_output=True)
        
        print(f"📥 Restaurando backup: {backup_file}")
        with open(backup_file, 'r') as f:
            result = subprocess.run(cmd_restore, stdin=f, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Backup restaurado com sucesso!")
            return True
        else:
            print(f"❌ Erro na restauração: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def download_production_data(prod_host, prod_user):
    """Baixa dados da produção via SSH"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    remote_backup = f"prod_backup_{timestamp}.sql"
    
    try:
        print(f"🌐 Conectando à produção: {prod_user}@{prod_host}")
        print("🔑 Você será solicitado a inserir a senha SSH...")
        
        # Comando para criar backup na produção
        print("📦 Criando backup na produção...")
        ssh_cmd = f'ssh {prod_user}@{prod_host} "docker exec quiz_db pg_dump -U quiz_user -d quiz --no-owner --no-privileges" > {remote_backup}'
        result = os.system(ssh_cmd)
        
        if result == 0 and os.path.exists(remote_backup):
            print(f"✅ Backup baixado: {remote_backup}")
            return remote_backup
        else:
            print("❌ Falha no backup")
            return None
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("""
🔧 Sistema de Backup/Restore PsicoQuiz

Uso:
  python backup_restore.py backup          # Criar backup local
  python backup_restore.py export          # Exportar para JSON
  python backup_restore.py restore <file>  # Restaurar backup
  python backup_restore.py sync <host> <user>  # Sincronizar com produção
        """)
        return
    
    command = sys.argv[1]
    
    if command == "backup":
        backup_database()
        export_json()
    
    elif command == "export":
        export_json()
    
    elif command == "restore":
        if len(sys.argv) < 3:
            print("❌ Especifique o arquivo de backup")
            return
        restore_database(sys.argv[2])
    
    elif command == "sync":
        if len(sys.argv) < 3:
            print("❌ Especifique o IP do servidor: python backup_restore.py sync IP [usuario]")
            print("Exemplo: python backup_restore.py sync 192.168.1.100")
            return
        
        host = sys.argv[2]
        user = sys.argv[3] if len(sys.argv) > 3 else "root"
        
        print(f"🔗 Conectando em: {user}@{host}")
        backup_file = download_production_data(host, user)
        
        if backup_file:
            print("\n🔄 Restaurar dados baixados? (y/N): ", end="")
            if input().lower() == 'y':
                restore_database(backup_file)
    
    else:
        print(f"❌ Comando desconhecido: {command}")

if __name__ == '__main__':
    main()
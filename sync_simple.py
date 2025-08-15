#!/usr/bin/env python3
"""
Script simples para sincronizar com VPS usando SSH por senha
"""
import os
import sys
from datetime import datetime

def sync_with_vps():
    # Solicita dados do servidor
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    else:
        server_ip = input("Digite o IP do servidor: ")
    
    user = "root"  # Padrão conforme seu uso
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"vps_backup_{timestamp}.sql"
    
    print(f"🌐 Conectando em: {user}@{server_ip}")
    print("🔑 Digite a senha quando solicitado...")
    
    # Comando SSH direto para criar e baixar backup
    ssh_command = f'''ssh {user}@{server_ip} "cd /root && docker exec quiz_db pg_dump -U quiz_user -d quiz --no-owner --no-privileges"'''
    
    print("📦 Criando e baixando backup...")
    result = os.system(f"{ssh_command} > {backup_file}")
    
    if result == 0 and os.path.exists(backup_file):
        # Verifica se arquivo não está vazio
        if os.path.getsize(backup_file) > 100:
            print(f"✅ Backup baixado: {backup_file}")
            
            # Pergunta se quer restaurar
            restore = input("\n🔄 Restaurar dados no ambiente local? (y/N): ")
            if restore.lower() == 'y':
                print("🔄 Restaurando backup...")
                
                # Para containers locais
                os.system("docker-compose down")
                
                # Remove volume do banco para limpeza completa
                os.system("docker volume rm comport_quiz_data 2>nul")
                
                # Inicia apenas o banco
                os.system("docker-compose up -d db")
                os.system("timeout 10")  # Aguarda banco inicializar
                
                # Restaura backup
                restore_cmd = f'docker exec -i quiz_db psql -U quiz_user -d quiz < {backup_file}'
                restore_result = os.system(restore_cmd)
                
                if restore_result == 0:
                    print("✅ Dados restaurados com sucesso!")
                    
                    # Reinicia aplicação
                    os.system("docker-compose up -d")
                    print("🚀 Aplicação reiniciada!")
                else:
                    print("❌ Erro na restauração")
            
        else:
            print("❌ Arquivo de backup vazio ou inválido")
            os.remove(backup_file)
    else:
        print("❌ Falha no download do backup")

if __name__ == '__main__':
    sync_with_vps()
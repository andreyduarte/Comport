#!/usr/bin/env python3
"""
Sistema de Backup Automático
"""
import os
import schedule
import time
import shutil
from datetime import datetime, timedelta
from backup_restore import backup_database, export_json

# Configurações
BACKUP_DIR = "backups"
MAX_BACKUPS = 30  # Manter últimos 30 backups
BACKUP_TIMES = ["02:00", "14:00"]  # Backup às 2h e 14h

def setup_backup_dir():
    """Cria diretório de backups"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"📁 Diretório criado: {BACKUP_DIR}")

def cleanup_old_backups():
    """Remove backups antigos"""
    try:
        files = []
        for f in os.listdir(BACKUP_DIR):
            if f.startswith("backup_") and f.endswith(".sql"):
                filepath = os.path.join(BACKUP_DIR, f)
                files.append((filepath, os.path.getctime(filepath)))
        
        # Ordena por data de criação
        files.sort(key=lambda x: x[1], reverse=True)
        
        # Remove arquivos excedentes
        if len(files) > MAX_BACKUPS:
            for filepath, _ in files[MAX_BACKUPS:]:
                os.remove(filepath)
                print(f"🗑️ Backup antigo removido: {os.path.basename(filepath)}")
    
    except Exception as e:
        print(f"❌ Erro na limpeza: {e}")

def run_backup():
    """Executa backup completo"""
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Iniciando backup automático...")
    
    setup_backup_dir()
    
    # Backup SQL
    sql_file = backup_database()
    if sql_file:
        # Move para diretório de backups
        dest_sql = os.path.join(BACKUP_DIR, os.path.basename(sql_file))
        shutil.move(sql_file, dest_sql)
        print(f"📦 SQL backup: {dest_sql}")
    
    # Backup JSON
    json_file = export_json()
    if json_file:
        dest_json = os.path.join(BACKUP_DIR, os.path.basename(json_file))
        shutil.move(json_file, dest_json)
        print(f"📄 JSON backup: {dest_json}")
    
    # Limpeza
    cleanup_old_backups()
    print("✅ Backup automático concluído!\n")

def start_scheduler():
    """Inicia agendador de backups"""
    print("🤖 Iniciando sistema de backup automático...")
    print(f"⏰ Horários configurados: {', '.join(BACKUP_TIMES)}")
    print(f"📁 Diretório: {BACKUP_DIR}")
    print(f"🗂️ Máximo de backups: {MAX_BACKUPS}")
    
    # Agenda backups
    for backup_time in BACKUP_TIMES:
        schedule.every().day.at(backup_time).do(run_backup)
    
    # Backup inicial (opcional)
    print("\n🚀 Executando backup inicial...")
    run_backup()
    
    # Loop principal
    print("⏳ Aguardando próximo backup...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica a cada minuto

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "now":
        # Backup imediato
        run_backup()
    else:
        # Modo daemon
        try:
            start_scheduler()
        except KeyboardInterrupt:
            print("\n👋 Sistema de backup interrompido")
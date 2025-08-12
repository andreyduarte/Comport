#!/usr/bin/env python3
"""
Script para gerenciar migrações do banco de dados
"""
import os
import sys
from flask_migrate import init, migrate, upgrade, downgrade
from app import app, db

def init_migrations():
    """Inicializa o sistema de migrações"""
    with app.app_context():
        try:
            # Garante que a pasta migrations existe
            os.makedirs('migrations', exist_ok=True)
            init()
            print("Sistema de migrações inicializado!")
        except Exception as e:
            print(f"Erro ao inicializar migrações: {e}")

def create_migration(message="Auto migration"):
    """Cria uma nova migração"""
    with app.app_context():
        try:
            migrate(message=message)
            print(f"Migração criada: {message}")
        except Exception as e:
            print(f"Erro ao criar migração: {e}")

def apply_migrations():
    """Aplica todas as migrações pendentes"""
    with app.app_context():
        try:
            upgrade()
            print("Migrações aplicadas com sucesso!")
        except Exception as e:
            print(f"Erro ao aplicar migrações: {e}")

def rollback_migration():
    """Desfaz a última migração"""
    with app.app_context():
        try:
            downgrade()
            print("Migração desfeita!")
        except Exception as e:
            print(f"Erro ao desfazer migração: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python migrate.py [init|create|apply|rollback] [mensagem]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
        init_migrations()
    elif command == "create":
        message = sys.argv[2] if len(sys.argv) > 2 else "Auto migration"
        create_migration(message)
    elif command == "apply":
        apply_migrations()
    elif command == "rollback":
        rollback_migration()
    else:
        print("Comando inválido. Use: init, create, apply ou rollback")
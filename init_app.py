#!/usr/bin/env python3
"""
Script de inicialização da aplicação
Executa todas as configurações necessárias antes de iniciar o servidor
"""
import os
import sys
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

def main():
    print("🚀 Inicializando PsicoQuiz...")
    
    try:
        # Importa após carregar .env
        from app import app, init_db, migrate_from_json, create_teacher_account
        
        print("📊 Inicializando banco de dados...")
        if init_db():
            print("✅ Banco inicializado com sucesso!")
            
            print("📦 Migrando dados do JSON...")
            migrate_from_json()
            
            print("👨🏫 Criando conta de professor...")
            create_teacher_account()
            
            # Verifica se a conta foi criada
            with app.app_context():
                from models import User
                teacher_username = os.getenv('TEACHER_USERNAME', 'professor')
                teacher = User.query.get(teacher_username)
                
                if teacher and teacher.is_teacher:
                    print(f"✅ Conta professor '{teacher_username}' está ativa!")
                    print(f"   - Senha: {os.getenv('TEACHER_PASSWORD', 'admin123')}")
                    print(f"   - Turma: {teacher.turma}")
                else:
                    print(f"❌ Problema com conta professor '{teacher_username}'")
                    sys.exit(1)
            
            print("🎉 Inicialização concluída com sucesso!")
            return True
        else:
            print("❌ Falha ao inicializar banco de dados")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
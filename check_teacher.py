#!/usr/bin/env python3
"""
Script para verificar e corrigir conta de professor
Execute: docker exec -it psicoquiz python check_teacher.py
"""
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

def check_and_fix_teacher():
    from app import app
    from models import db, User
    
    with app.app_context():
        print("🔍 Verificando contas de professor...")
        
        # Dados do .env
        teacher_username = os.getenv('TEACHER_USERNAME', 'professor')
        teacher_password = os.getenv('TEACHER_PASSWORD', 'admin123')
        teacher_turma = os.getenv('TEACHER_TURMA', 'Docente')
        
        print(f"📋 Configuração do .env:")
        print(f"   - Username: {teacher_username}")
        print(f"   - Password: {teacher_password}")
        print(f"   - Turma: {teacher_turma}")
        
        # Verifica conta existente
        teacher = User.query.get(teacher_username)
        
        if teacher:
            print(f"\n✅ Usuário '{teacher_username}' encontrado:")
            print(f"   - É professor: {teacher.is_teacher}")
            print(f"   - Turma: {teacher.turma}")
            print(f"   - Senha: {teacher.senha}")
            
            if not teacher.is_teacher:
                print("🔧 Corrigindo flag is_teacher...")
                teacher.is_teacher = True
                db.session.commit()
                print("✅ Corrigido!")
                
        else:
            print(f"\n❌ Usuário '{teacher_username}' não encontrado!")
            print("🔧 Criando conta...")
            
            new_teacher = User(
                username=teacher_username,
                senha=teacher_password,
                turma=teacher_turma,
                pontuacao=0,
                combo=0,
                max_combo=0,
                is_teacher=True
            )
            db.session.add(new_teacher)
            db.session.commit()
            print("✅ Conta criada!")
        
        # Lista todos os professores
        print("\n👨🏫 Todos os professores no sistema:")
        teachers = User.query.filter_by(is_teacher=True).all()
        if teachers:
            for t in teachers:
                print(f"   - {t.username} ({t.turma}) - Senha: {t.senha}")
        else:
            print("   Nenhum professor encontrado!")
        
        # Lista todos os usuários
        print(f"\n👥 Total de usuários: {User.query.count()}")
        all_users = User.query.limit(5).all()
        for u in all_users:
            print(f"   - {u.username} (Professor: {u.is_teacher})")

if __name__ == '__main__':
    check_and_fix_teacher()
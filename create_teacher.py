#!/usr/bin/env python3
"""
Script para criar conta de professor manualmente
"""
import os
from dotenv import load_dotenv
from app import app, db, User

# Carrega variáveis do .env
load_dotenv()

def create_teacher():
    with app.app_context():
        # Dados do professor do .env
        teacher_username = os.getenv('TEACHER_USERNAME', 'professor')
        teacher_password = os.getenv('TEACHER_PASSWORD', 'admin123')
        teacher_turma = os.getenv('TEACHER_TURMA', 'Docente')
        
        print(f"🔍 Verificando conta: {teacher_username}")
        print(f"📧 Senha: {teacher_password}")
        print(f"🏫 Turma: {teacher_turma}")
        
        # Verifica se já existe
        existing = User.query.get(teacher_username)
        
        if existing:
            print(f"ℹ️ Usuário '{teacher_username}' já existe")
            print(f"   - É professor: {existing.is_teacher}")
            print(f"   - Turma: {existing.turma}")
            
            if not existing.is_teacher:
                existing.is_teacher = True
                db.session.commit()
                print("✅ Conta atualizada para professor!")
            else:
                print("✅ Conta já é de professor!")
        else:
            # Cria nova conta
            teacher = User(
                username=teacher_username,
                senha=teacher_password,
                turma=teacher_turma,
                pontuacao=0,
                combo=0,
                max_combo=0,
                is_teacher=True
            )
            db.session.add(teacher)
            db.session.commit()
            print(f"✅ Conta professor '{teacher_username}' criada com sucesso!")
        
        # Lista todos os professores
        print("\n👨‍🏫 Professores no sistema:")
        teachers = User.query.filter_by(is_teacher=True).all()
        for t in teachers:
            print(f"   - {t.username} ({t.turma})")

if __name__ == '__main__':
    create_teacher()
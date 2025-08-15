from functools import wraps
from flask import session, redirect, url_for, flash
from models import User, UserQuestion, AdminLog, db
from sqlalchemy import func, desc
from datetime import datetime, timedelta

def admin_required(f):
    """Decorator para proteger rotas administrativas"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Acesso negado. Faça login primeiro.", "error")
            return redirect(url_for('login_register'))
        
        user = User.query.get(session['username'])
        if not user or not user.is_teacher:
            flash("Acesso negado. Apenas professores podem acessar esta área.", "error")
            return redirect(url_for('perfil'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_admin_stats():
    """Retorna estatísticas básicas para o dashboard"""
    from app import ALL_QUESTIONS
    
    total_students = User.query.filter_by(is_teacher=False).count()
    total_questions_answered = UserQuestion.query.count()
    
    # Alunos ativos nos últimos 7 dias (aproximação baseada em questões respondidas)
    week_ago = datetime.now() - timedelta(days=7)
    # Como não temos timestamp nas questões, vamos usar uma aproximação
    active_students = User.query.filter_by(is_teacher=False).filter(User.pontuacao > 0).count()
    
    # Questões mais erradas
    wrong_questions = db.session.query(
        UserQuestion.question_id,
        func.count(UserQuestion.question_id).label('wrong_count')
    ).filter_by(is_correct=False).group_by(
        UserQuestion.question_id
    ).order_by(desc('wrong_count')).limit(10).all()
    
    # Distribuição por turma
    turma_stats = db.session.query(
        User.turma,
        func.count(User.username).label('count'),
        func.avg(User.pontuacao).label('avg_score')
    ).filter_by(is_teacher=False).group_by(User.turma).all()
    
    # Criar dicionário de questões para lookup
    questions_dict = {q['id']: q for q in ALL_QUESTIONS}
    
    return {
        'total_students': total_students,
        'total_questions_answered': total_questions_answered,
        'active_students': active_students,
        'wrong_questions': wrong_questions,
        'turma_stats': turma_stats,
        'questions_dict': questions_dict
    }

def get_student_list(turma_filter=None, search=None, page=1, per_page=20):
    """Retorna lista paginada de alunos com filtros"""
    query = User.query.filter_by(is_teacher=False)
    
    if turma_filter:
        query = query.filter_by(turma=turma_filter)
    
    if search:
        query = query.filter(User.username.contains(search))
    
    return query.order_by(desc(User.pontuacao)).paginate(
        page=page, per_page=per_page, error_out=False
    )

def get_all_turmas():
    """Retorna lista de todas as turmas"""
    return db.session.query(User.turma).filter_by(is_teacher=False).distinct().all()

def log_admin_action(admin_user, action, target_user, details=None):
    """Registra ação administrativa para auditoria"""
    from models import AdminLog, db
    from datetime import datetime
    
    try:
        log_entry = AdminLog(
            admin_username=admin_user,
            action=action,
            target_username=target_user,
            details=str(details) if details else None,
            timestamp=datetime.now()
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"Erro ao registrar log: {e}")
        db.session.rollback()
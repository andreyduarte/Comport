import json
import random
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_migrate import Migrate
from models import db, User, UserQuestion, UserAchievement

# Configuração do banco PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://quiz_user:quiz_pass@localhost:5432/quiz')

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

def init_db():
    """Inicializa o banco de dados com migrações"""
    try:
        with app.app_context():
            # Sempre cria tabelas diretamente (mais confiável)
            db.create_all()
            print("Tabelas criadas com sucesso!")
            return True
    except Exception as e:
        print(f"Erro ao inicializar banco: {e}")
        return False

def migrate_from_json():
    """Migra dados do JSON para PostgreSQL"""
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        with app.app_context():
            for username, data in users_data.items():
                # Verifica se usuário já existe
                user = User.query.get(username)
                if not user:
                    user = User(
                        username=username,
                        senha=data.get('senha', ''),
                        turma=data.get('turma', ''),
                        pontuacao=data.get('pontuacao', 0),
                        combo=data.get('combo', 0),
                        max_combo=data.get('max_combo', data.get('combo', 0)),
                        is_teacher=data.get('is_teacher', False)
                    )
                    db.session.add(user)
                
                # Migra questões respondidas
                for q_id in data.get('answered_questions', []):
                    is_correct = q_id in data.get('correct_questions', [])
                    existing = UserQuestion.query.filter_by(username=username, question_id=q_id).first()
                    if not existing:
                        question = UserQuestion(username=username, question_id=q_id, is_correct=is_correct)
                        db.session.add(question)
                
                # Migra achievements
                for achievement in data.get('achievements', []):
                    existing = UserAchievement.query.filter_by(username=username, achievement_key=achievement).first()
                    if not existing:
                        ach = UserAchievement(username=username, achievement_key=achievement)
                        db.session.add(ach)
            
            db.session.commit()
            print("Migração do JSON para PostgreSQL concluída!")
        
    except FileNotFoundError:
        print("Arquivo users.json não encontrado, pulando migração.")
    except Exception as e:
        print(f"Erro na migração: {e}")
        with app.app_context():
            db.session.rollback()

def create_teacher_account():
    """Cria conta de professor se não existir"""
    teacher_username = os.getenv('TEACHER_USERNAME', 'professor')
    teacher_password = os.getenv('TEACHER_PASSWORD', 'admin123')
    teacher_turma = os.getenv('TEACHER_TURMA', 'Docente')
    
    with app.app_context():
        if not User.query.get(teacher_username):
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
            print(f"Conta de professor '{teacher_username}' criada com sucesso!")

def load_questions():
    with open('QUESTOES.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)
    for i, q in enumerate(questions):
        q['id'] = i
        # Adiciona temas baseados em palavras-chave
        if any(word in q['pergunta'].lower() for word in ['pavlov', 'sino', 'salivação', 'condicionado', 'incondicionado']):
            q['tema'] = 'pavlov'
        elif any(word in q['pergunta'].lower() for word in ['watson', 'albert', 'medo']):
            q['tema'] = 'watson'
        elif any(word in q['pergunta'].lower() for word in ['reflexo', 'estímulo', 'resposta', 'elicia']):
            q['tema'] = 'reflexos'
        elif any(word in q['pergunta'].lower() for word in ['extinção', 'generalização', 'recuperação']):
            q['tema'] = 'processos'
        else:
            q['tema'] = 'geral'
    return questions

ALL_QUESTIONS = load_questions()

def get_achievements():
    return {
        # Achievements baseados em questões respondidas
        'primeiro_passo':    {'name': 'Primeiro Passo',      'desc': 'Responda 5 questões',         'icon': '🎆', 'type': 'questions',      'threshold': 5},
        'estudioso':         {'name': 'Estudioso',           'desc': 'Responda 20 questões',        'icon': '🌟', 'type': 'questions',      'threshold': 20},
        'expert':            {'name': 'Expert',              'desc': 'Responda 50 questões',        'icon': '🐭', 'type': 'questions',      'threshold': 50},
        'mestre':            {'name': 'Mestre',              'desc': 'Responda 100 questões',       'icon': '👑', 'type': 'questions',      'threshold': 100},
        'dedicado':          {'name': 'Dedicado',            'desc': 'Responda 150 questões',       'icon': '📚', 'type': 'questions',      'threshold': 150},
        'incansavel':        {'name': 'Incansável',          'desc': 'Responda 200 questões',       'icon': '🚀', 'type': 'questions',      'threshold': 200},
        'lenda':             {'name': 'Lenda',               'desc': 'Responda 300 questões',       'icon': '🏛️', 'type': 'questions',      'threshold': 300},
        
        # Achievements de ranking
        'top10':             {'name': 'Top 10',              'desc': 'Fique entre os 10 primeiros', 'icon': '🥉', 'type': 'rank',           'threshold': 10},
        'top5':              {'name': 'Top 5',               'desc': 'Fique entre os 5 primeiros',  'icon': '🥈', 'type': 'rank',           'threshold': 5},
        'top3':              {'name': 'Top 3',               'desc': 'Fique entre os 3 primeiros',  'icon': '🥇', 'type': 'rank',           'threshold': 3},
        'campeao':           {'name': 'Campeão',             'desc': 'Seja o 1º colocado',          'icon': '🏆', 'type': 'rank',           'threshold': 1},
        
        # Achievements de combo
        'combo_fire':        {'name': 'Em Chamas',           'desc': 'Combo 10x',                   'icon': '🔥', 'type': 'combo',          'threshold': 10},
        'combo_master':      {'name': 'Combo Master',        'desc': 'Combo 25x',                   'icon': '⚡', 'type': 'combo',          'threshold': 25},
        'speed_demon':       {'name': 'Demônio da Velocidade','desc': 'Combo 15x',                   'icon': '💨', 'type': 'combo',          'threshold': 15},
        'combo_legend':      {'name': 'Lenda do Combo',      'desc': 'Combo 50x',                   'icon': '🌟', 'type': 'combo',          'threshold': 50},
        'combo_god':         {'name': 'Deus do Combo',       'desc': 'Combo 100x',                  'icon': '👑', 'type': 'combo',          'threshold': 100},
        
        # Achievements temáticos
        'pavlov_expert':     {'name': 'Pavlov Expert',       'desc': 'Acerte 10 sobre Pavlov',      'icon': '🐕', 'type': 'theme',          'theme': 'pavlov',   'threshold': 10},
        'watson_master':     {'name': 'Watson Master',       'desc': 'Acerte 5 sobre Watson',       'icon': '👶', 'type': 'theme',          'theme': 'watson',   'threshold': 5},
        'reflexos_pro':      {'name': 'Reflexos Pro',        'desc': 'Acerte 15 sobre reflexos',    'icon': '⚡', 'type': 'theme',          'theme': 'reflexos', 'threshold': 15},
        
        # Achievements especiais
        'completionist':     {'name': 'Completista',         'desc': 'Responda todas as questões',  'icon': '💯', 'type': 'completionist'},
        'perfect_start':     {'name': 'Início Perfeito',     'desc': 'Acerte as 5 primeiras',       'icon': '🎯', 'type': 'perfect_start',  'threshold': 5}
    }

def check_achievement_condition(achievement, user_data):
    """Check if a user meets the condition for a specific achievement."""
    a_type    = achievement.get('type')
    threshold = achievement.get('threshold', 0)

    if a_type == 'questions':
        return len(user_data.get('answered_questions', [])) >= threshold
    elif a_type == 'rank':
        return user_data.get('rank', 999) <= threshold
    elif a_type == 'combo':
        return user_data.get('max_combo', 0) >= threshold
    elif a_type == 'theme':
        theme = achievement.get('theme')
        count = sum(
            1
            for q_id in user_data.get('correct_questions', [])
            if next((q for q in ALL_QUESTIONS if q['id'] == q_id), {}).get('tema') == theme
        )
        return count >= threshold
    elif a_type == 'completionist':
        return len(user_data.get('correct_questions', [])) >= len(ALL_QUESTIONS)
    elif a_type == 'perfect_start':
        combo    = user_data.get('combo', 0)
        answered = len(user_data.get('answered_questions', []))
        return combo >= threshold and answered == combo

    return False

def check_new_achievements(user_data, rank=999):
    achievements = get_achievements()
    user_achievements = set(user_data.get('achievements', []))
    user_data['rank'] = rank
    
    new_achievements = []
    for key, achievement in achievements.items():
        if key not in user_achievements and check_achievement_condition(achievement, user_data):
            new_achievements.append(achievement)
    
    return new_achievements

def get_user(username):
    """Busca um usuário no banco"""
    try:
        user = User.query.get(username)
        if user:
            return user.to_dict()
        return None
    except Exception as e:
        print(f"Erro ao buscar usuário: {e}")
        return None

def save_user(username, user_data):
    """Salva um usuário no banco"""
    try:
        user = User.query.get(username)
        if user:
            # Atualiza usuário existente
            user.senha = user_data.get('senha', user.senha)
            user.turma = user_data.get('turma', user.turma)
            user.pontuacao = user_data.get('pontuacao', user.pontuacao)
            user.combo = user_data.get('combo', user.combo)
            user.max_combo = user_data.get('max_combo', user.max_combo)
            user.is_teacher = user_data.get('is_teacher', user.is_teacher)
        else:
            # Cria novo usuário
            user = User(
                username=username,
                senha=user_data.get('senha', ''),
                turma=user_data.get('turma', ''),
                pontuacao=user_data.get('pontuacao', 0),
                combo=user_data.get('combo', 0),
                max_combo=user_data.get('max_combo', 0),
                is_teacher=user_data.get('is_teacher', False)
            )
            db.session.add(user)
        
        db.session.commit()
    except Exception as e:
        print(f"Erro ao salvar usuário: {e}")
        db.session.rollback()

def get_all_users():
    """Busca todos os usuários"""
    try:
        users = User.query.order_by(User.pontuacao.desc()).all()
        return [{'nome': u.username, 'turma': u.turma, 'pontuacao': u.pontuacao} for u in users]
    except Exception as e:
        print(f"Erro ao buscar usuários: {e}")
        return []

def add_user_question(username, question_id, is_correct):
    """Adiciona uma questão respondida"""
    try:
        existing = UserQuestion.query.filter_by(username=username, question_id=question_id).first()
        if not existing:
            question = UserQuestion(username=username, question_id=question_id, is_correct=is_correct)
            db.session.add(question)
            db.session.commit()
    except Exception as e:
        print(f"Erro ao adicionar questão: {e}")
        db.session.rollback()

def add_user_achievement(username, achievement_key):
    """Adiciona um achievement"""
    try:
        existing = UserAchievement.query.filter_by(username=username, achievement_key=achievement_key).first()
        if not existing:
            achievement = UserAchievement(username=username, achievement_key=achievement_key)
            db.session.add(achievement)
            db.session.commit()
    except Exception as e:
        print(f"Erro ao adicionar achievement: {e}")
        db.session.rollback()

@app.route('/', methods=['GET', 'POST'])
def login_register():
    if 'username' in session:
        return redirect(url_for('perfil'))
        
    if request.method == 'POST':
        username = request.form['nome'].strip()
        password = request.form['senha']
        action = request.form.get('action')

        if action == 'register':
            turma = request.form['turma']
            if not username or not password or not turma:
                flash("Todos os campos são obrigatórios para o cadastro!", "error")
                return redirect(url_for('login_register'))
            if get_user(username):
                flash("Este nome de usuário já existe!", "error")
                return redirect(url_for('login_register'))

            save_user(username, {
                'senha': password, 
                'turma': turma, 
                'pontuacao': 0, 
                'combo': 0, 
                'max_combo': 0
            })
            session['username'] = username
            session['pontuacao'] = 0
            session['combo'] = 0
            flash(f"Bem-vindo(a), {username}! 🎉 Vamos começar a aprender!", "success")
            return redirect(url_for('perfil'))

        elif action == 'login':
            user = get_user(username)
            if user and user['senha'] == password:
                session['username'] = username
                session['pontuacao'] = user['pontuacao']
                session['combo'] = user.get('combo', 0)
                session.pop('answered_ids', None)
                return redirect(url_for('perfil'))
            else:
                flash("Nome de usuário ou senha incorretos. 😅", "error")
                return redirect(url_for('login_register'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for('login_register'))

@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'username' not in session:
        return redirect(url_for('login_register'))

    username = session['username']
    user_data = get_user(username)
    
    if not user_data:
        flash("Usuário não encontrado. Faça login novamente.", "error")
        session.clear()
        return redirect(url_for('login_register'))
    
    # Atualiza a pontuação e combo na sessão
    session['pontuacao'] = user_data['pontuacao']
    session['combo'] = user_data.get('combo', 0)

    if request.method == 'POST':
        user_data['turma'] = request.form.get('turma', user_data['turma'])
        nova_senha = request.form.get('senha')
        if nova_senha:
            user_data['senha'] = nova_senha
        
        save_user(username, user_data)
        flash("Perfil atualizado com sucesso! ✨", "success")
        return redirect(url_for('perfil'))

    all_users = get_all_users()
    user_rank = next((i+1 for i, u in enumerate(all_users) if u['nome'] == username), -1)

    achievements = get_achievements()
    user_achievements = {key: achievements[key] for key in user_data.get('achievements', []) if key in achievements}
    
    # Calcula porcentagem de questões completadas
    total_questions = len(ALL_QUESTIONS)
    answered_questions = len(user_data.get('answered_questions', []))
    completion_percentage = round((answered_questions / total_questions) * 100, 1) if total_questions > 0 else 0
    
    return render_template('perfil.html', user=user_data, rank=user_rank, username=username, 
                         achievements=user_achievements, completion_percentage=completion_percentage,
                         answered_questions=answered_questions, total_questions=total_questions)

@app.route('/ranking')
def ranking():
    if 'username' not in session:
        return redirect(url_for('login_register'))
        
    current_user = get_user(session['username'])
    current_turma = current_user.get('turma', '') if current_user else ''
    
    filter_type = request.args.get('filter', 'geral')
    
    user_list = get_all_users()
    
    if filter_type == 'turma' and current_turma:
        user_list = [user for user in user_list if user.get('turma') == current_turma]
    
    sorted_users = user_list
    
    return render_template('ranking.html', users=sorted_users, filter_type=filter_type, current_turma=current_turma)

@app.route('/usuario/<username>')
def ver_usuario(username):
    if 'username' not in session:
        return redirect(url_for('login_register'))
    
    user_data = get_user(username)
    
    if not user_data:
        flash("Usuário não encontrado! 😅", "error")
        return redirect(url_for('ranking'))
    
    # Calcula ranking
    all_users = get_all_users()
    user_rank = next((i+1 for i, u in enumerate(all_users) if u['nome'] == username), -1)
    
    achievements = get_achievements()
    user_achievements = {key: achievements[key] for key in user_data.get('achievements', []) if key in achievements}
    
    return render_template('usuario.html', user=user_data, rank=user_rank, username=username, achievements=user_achievements)

@app.route('/live-ranking')
def live_ranking():
    user_list = get_all_users()[:100]
    sorted_users = user_list
    return render_template('live_ranking.html', users=sorted_users)

@app.route('/jogar')
def jogar():
    if 'username' not in session:
        return redirect(url_for('login_register'))
    
    user_data = get_user(session['username']) or {}
    correct_questions = set(user_data.get('correct_questions', []))
    
    # Se acertou todas, permite repetir
    if len(correct_questions) >= len(ALL_QUESTIONS):
        available_questions = ALL_QUESTIONS.copy()
    else:
        available_questions = [q for q in ALL_QUESTIONS if q['id'] not in correct_questions]
    
    if not available_questions:
        flash("🎉 Parabéns! Você completou todas as questões! Você é um expert em Análise do Comportamento!", "success")
        return redirect(url_for('perfil'))
    
    question = random.choice(available_questions)
    
    # Randomiza as opções
    opcoes_list = list(question['opcoes'].items())
    random.shuffle(opcoes_list)
    question['opcoes_randomizadas'] = opcoes_list
    
    return render_template('jogar.html', question=question)

@app.route('/responder', methods=['POST'])
def responder():
    if 'username' not in session:
        return redirect(url_for('login_register'))
        
    question_id = int(request.form['question_id'])
    user_answer = request.form.get('opcao')

    question = next((q for q in ALL_QUESTIONS if q['id'] == question_id), None)
    
    if not question:
        flash("Questão não encontrada! 😅", "error")
        return redirect(url_for('jogar'))

    answered_ids = session.get('answered_ids', [])
    if question_id not in answered_ids:
        answered_ids.append(question_id)
        session['answered_ids'] = answered_ids

    is_correct = (user_answer == question['resposta_correta'])
    
    username = session['username']
    user_data = get_user(username)
    
    if not user_data:
        flash("Erro ao carregar dados do usuário", "error")
        return redirect(url_for('login_register'))
        
    current_combo = session.get('combo', 0)
    
    # Adiciona questão respondida
    add_user_question(username, question_id, is_correct)
    
    # Recarrega dados do usuário após adicionar questão
    user_data = get_user(username)
    if not user_data:
        flash("Erro ao recarregar dados do usuário", "error")
        return redirect(url_for('login_register'))
    
    new_achievements = []
    
    if is_correct:
        # Aumenta combo
        current_combo += 1
        session['combo'] = current_combo
        user_data['combo'] = current_combo
        
        # Atualiza max_combo se necessário
        if current_combo > user_data.get('max_combo', 0):
            user_data['max_combo'] = current_combo
        
        # Calcula bônus de moedas (1% por combo, máx 50%)
        combo_bonus = min(current_combo, 50) / 100
        base_coins = 10
        bonus_coins = int(base_coins * combo_bonus)
        total_coins = base_coins + bonus_coins
        
        user_data['pontuacao'] += total_coins
        session['pontuacao'] = user_data['pontuacao']
        
        # Calcula bônus de tempo
        if current_combo >= 10:
            time_bonus = 10
        elif current_combo >= 5:
            time_bonus = 5
        else:
            time_bonus = 0
            
        session['coins_earned'] = total_coins
        session['combo_bonus'] = combo_bonus * 100
        session['time_bonus'] = time_bonus
        
        # Calcula ranking para achievements
        all_users = get_all_users()
        user_rank = next((i+1 for i, u in enumerate(all_users) if u['nome'] == username), 999)
        
        # Verifica novos achievements
        new_achievements = check_new_achievements(user_data, user_rank)
        
        # Adiciona novos achievements ao banco
        for achievement in new_achievements:
            for key, ach_data in get_achievements().items():
                if ach_data == achievement:
                    add_user_achievement(username, key)
                    break
        
    else:
        # Reset combo
        session['combo'] = 0
        if user_data:
            user_data['combo'] = 0
    
    save_user(username, user_data)
    
    session['new_achievements'] = new_achievements

    correct_option_text = question['opcoes'][question['resposta_correta']]
    
    return render_template('resultado.html', 
                           is_correct=is_correct, 
                           correct_answer=correct_option_text,
                           question=question,
                           new_achievements=new_achievements)

if __name__ == '__main__':
    if init_db():
        migrate_from_json()
        create_teacher_account()
    else:
        print("Falha ao inicializar banco de dados")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
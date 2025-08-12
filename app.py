import json
import random
import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash

# Configuração do banco PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://quiz_user:quiz_pass@localhost:5432/quiz')

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this'

def init_db():
    """Inicializa o banco de dados"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(50) PRIMARY KEY,
            senha VARCHAR(255) NOT NULL,
            turma VARCHAR(100) NOT NULL,
            pontuacao INTEGER DEFAULT 0,
            combo INTEGER DEFAULT 0,
            max_combo INTEGER DEFAULT 0,
            is_teacher BOOLEAN DEFAULT FALSE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_questions (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50),
            question_id INTEGER,
            is_correct BOOLEAN,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_achievements (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50),
            achievement_key VARCHAR(50),
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    
    conn.commit()
    conn.close()

def migrate_from_json():
    """Migra dados do JSON para PostgreSQL"""
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
        except psycopg2.Error as e:
            print(f"Erro na migração: {e}")
            return
        
        for username, data in users_data.items():
            cursor.execute('''
                INSERT INTO users 
                (username, senha, turma, pontuacao, combo, max_combo, is_teacher)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE SET
                senha = EXCLUDED.senha,
                turma = EXCLUDED.turma,
                pontuacao = EXCLUDED.pontuacao,
                combo = EXCLUDED.combo,
                max_combo = EXCLUDED.max_combo,
                is_teacher = EXCLUDED.is_teacher
            ''', (
                username,
                data.get('senha', ''),
                data.get('turma', ''),
                data.get('pontuacao', 0),
                data.get('combo', 0),
                data.get('max_combo', data.get('combo', 0)),
                data.get('is_teacher', False)
            ))
            
            # Migra questões respondidas
            for q_id in data.get('answered_questions', []):
                is_correct = q_id in data.get('correct_questions', [])
                cursor.execute('''
                    INSERT INTO user_questions 
                    (username, question_id, is_correct) VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                ''', (username, q_id, is_correct))
            
            # Migra achievements
            for achievement in data.get('achievements', []):
                cursor.execute('''
                    INSERT INTO user_achievements 
                    (username, achievement_key) VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                ''', (username, achievement))
        
        conn.commit()
        conn.close()
        print("Migração do JSON para PostgreSQL concluída!")
        
    except FileNotFoundError:
        print("Arquivo users.json não encontrado, pulando migração.")

def create_teacher_account():
    """Cria conta de professor se não existir"""
    teacher_username = os.getenv('TEACHER_USERNAME', 'professor')
    teacher_password = os.getenv('TEACHER_PASSWORD', 'admin123')
    teacher_turma = os.getenv('TEACHER_TURMA', 'Docente')
    
    if not get_user(teacher_username):
        save_user(teacher_username, {
            'senha': teacher_password,
            'turma': teacher_turma,
            'pontuacao': 0,
            'combo': 0,
            'max_combo': 0,
            'is_teacher': True
        })
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
            user_achievements.add(key)
            new_achievements.append(achievement)
    
    user_data['achievements'] = list(user_achievements)
    return new_achievements

def get_user(username):
    """Busca um usuário no banco"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user_row = cursor.fetchone()
        
        if not user_row:
            conn.close()
            return None
        
        # Busca questões respondidas
        cursor.execute('SELECT question_id, is_correct FROM user_questions WHERE username = %s', (username,))
        questions = cursor.fetchall()
        
        # Busca achievements
        cursor.execute('SELECT achievement_key FROM user_achievements WHERE username = %s', (username,))
        achievements = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'senha': user_row[1],
            'turma': user_row[2],
            'pontuacao': user_row[3],
            'combo': user_row[4],
            'max_combo': user_row[5],
            'is_teacher': bool(user_row[6]),
            'answered_questions': [q[0] for q in questions],
            'correct_questions': [q[0] for q in questions if q[1]],
            'achievements': achievements
        }
    except psycopg2.Error as e:
        print(f"Erro PostgreSQL: {e}")
        return None

def save_user(username, user_data):
    """Salva um usuário no banco"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users 
            (username, senha, turma, pontuacao, combo, max_combo, is_teacher)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (username) DO UPDATE SET
            senha = EXCLUDED.senha,
            turma = EXCLUDED.turma,
            pontuacao = EXCLUDED.pontuacao,
            combo = EXCLUDED.combo,
            max_combo = EXCLUDED.max_combo,
            is_teacher = EXCLUDED.is_teacher
        ''', (
            username,
            user_data.get('senha', ''),
            user_data.get('turma', ''),
            user_data.get('pontuacao', 0),
            user_data.get('combo', 0),
            user_data.get('max_combo', 0),
            user_data.get('is_teacher', False)
        ))
        
        conn.commit()
        conn.close()
    except psycopg2.Error as e:
        print(f"Erro ao salvar usuário: {e}")

def get_all_users():
    """Busca todos os usuários"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute('SELECT username, turma, pontuacao FROM users ORDER BY pontuacao DESC')
        users = cursor.fetchall()
        
        conn.close()
        
        return [{'nome': u[0], 'turma': u[1], 'pontuacao': u[2]} for u in users]
    except psycopg2.Error:
        return []

def add_user_question(username, question_id, is_correct):
    """Adiciona uma questão respondida"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_questions 
            (username, question_id, is_correct) VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        ''', (username, question_id, is_correct))
        
        conn.commit()
        conn.close()
    except psycopg2.Error as e:
        print(f"Erro ao adicionar questão: {e}")

def add_user_achievement(username, achievement_key):
    """Adiciona um achievement"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_achievements 
            (username, achievement_key) VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        ''', (username, achievement_key))
        
        conn.commit()
        conn.close()
    except psycopg2.Error as e:
        print(f"Erro ao adicionar achievement: {e}")

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
    current_combo = session.get('combo', 0)
    
    # Adiciona questão respondida
    add_user_question(username, question_id, is_correct)
    
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
        
        # Verifica novos achievements
        new_achievements = check_new_achievements(user_data)
        
        # Adiciona novos achievements ao banco
        for achievement in new_achievements:
            for key, ach_data in get_achievements().items():
                if ach_data == achievement:
                    add_user_achievement(username, key)
                    break
        
    else:
        # Reset combo
        session['combo'] = 0
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
    init_db()
    migrate_from_json()
    create_teacher_account()
    app.run(host='0.0.0.0', port=5000, debug=False)
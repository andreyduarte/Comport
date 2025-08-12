import json
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this'

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
        'primeiro_passo':    {'name': 'Primeiro Passo',      'desc': '10+ moedas',                  'icon': '🎆', 'type': 'score',          'threshold': 10},
        'estudioso':         {'name': 'Estudioso',           'desc': '50+ moedas',                  'icon': '🌟', 'type': 'score',          'threshold': 50},
        'expert':            {'name': 'Expert',              'desc': '100+ moedas',                 'icon': '🧠', 'type': 'score',          'threshold': 100},
        'mestre':            {'name': 'Mestre',              'desc': '200+ moedas',                 'icon': '👑', 'type': 'score',          'threshold': 200},
        'top3':              {'name': 'Top 3',               'desc': 'Ranking',                     'icon': '🏆', 'type': 'rank',           'threshold': 3},
        'combo_fire':        {'name': 'Em Chamas',           'desc': 'Combo 10x',                   'icon': '🔥', 'type': 'combo',          'threshold': 10},
        'combo_master':      {'name': 'Combo Master',        'desc': 'Combo 25x',                   'icon': '⚡', 'type': 'combo',          'threshold': 25},
        'pavlov_expert':     {'name': 'Pavlov Expert',       'desc': 'Acerte 10 sobre Pavlov',      'icon': '🐕', 'type': 'theme',          'theme': 'pavlov',   'threshold': 10},
        'watson_master':     {'name': 'Watson Master',       'desc': 'Acerte 5 sobre Watson',       'icon': '👶', 'type': 'theme',          'theme': 'watson',   'threshold': 5},
        'reflexos_pro':      {'name': 'Reflexos Pro',        'desc': 'Acerte 15 sobre reflexos',    'icon': '⚡', 'type': 'theme',          'theme': 'reflexos', 'threshold': 15},
        'completionist':     {'name': 'Completista',         'desc': 'Responda todas as questões', 'icon': '💯', 'type': 'completionist'},
        'perfect_start':     {'name': 'Início Perfeito',     'desc': 'Acerte as 5 primeiras',      'icon': '🎯', 'type': 'perfect_start',  'threshold': 5},
        'speed_demon':       {'name': 'Demônio da Velocidade','desc': 'Combo 15x',                   'icon': '💨', 'type': 'combo',          'threshold': 15}
    }

def check_achievement_condition(achievement, user_data):
    """Check if a user meets the condition for a specific achievement."""
    a_type    = achievement.get('type')
    threshold = achievement.get('threshold', 0)

    if a_type == 'score':
        return user_data.get('pontuacao', 0) >= threshold
    elif a_type == 'rank':
        return user_data.get('rank', 999) <= threshold
    elif a_type == 'combo':
        return user_data.get('combo', 0) >= threshold
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
        if key not in user_achievements and 'condition' in achievement and achievement['condition'](user_data):
            user_achievements.add(key)
            new_achievements.append(achievement)
    
    user_data['achievements'] = list(user_achievements)
    return new_achievements

def load_users():
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(users):
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

@app.route('/', methods=['GET', 'POST'])
def login_register():
    if 'username' in session:
        return redirect(url_for('perfil'))
        
    if request.method == 'POST':
        users = load_users()
        username = request.form['nome'].strip()
        password = request.form['senha']
        action = request.form.get('action')

        if action == 'register':
            turma = request.form['turma']
            if not username or not password or not turma:
                flash("Todos os campos são obrigatórios para o cadastro!", "error")
                return redirect(url_for('login_register'))
            if username in users:
                flash("Este nome de usuário já existe!", "error")
                return redirect(url_for('login_register'))

            users[username] = {
                'senha': password, 
                'turma': turma, 
                'pontuacao': 0, 
                'combo': 0, 
                'correct_questions': [], 
                'answered_questions': [], 
                'achievements': []
            }
            save_users(users)
            session['username'] = username
            session['pontuacao'] = 0
            session['combo'] = 0
            flash(f"Bem-vindo(a), {username}! 🎉 Vamos começar a aprender!", "success")
            return redirect(url_for('perfil'))

        elif action == 'login':
            user = users.get(username)
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

    users = load_users()
    username = session['username']
    user_data = users.get(username)
    
    # Atualiza a pontuação e combo na sessão
    session['pontuacao'] = user_data['pontuacao']
    session['combo'] = user_data.get('combo', 0)

    if request.method == 'POST':
        user_data['turma'] = request.form.get('turma', user_data['turma'])
        nova_senha = request.form.get('senha')
        if nova_senha:
            user_data['senha'] = nova_senha
        
        users[username] = user_data
        save_users(users)
        flash("Perfil atualizado com sucesso! ✨", "success")
        return redirect(url_for('perfil'))

    sorted_users = sorted(users.values(), key=lambda x: x['pontuacao'], reverse=True)
    user_rank = -1
    for i, u_data in enumerate(sorted_users):
        for name, data in users.items():
            if data == u_data and name == username:
                user_rank = i + 1
                break
        if user_rank != -1:
            break

    achievements = get_achievements()
    user_achievements = {key: achievements[key] for key in user_data.get('achievements', []) if key in achievements}
    
    return render_template('perfil.html', user=user_data, rank=user_rank, username=username, achievements=user_achievements)

@app.route('/ranking')
def ranking():
    if 'username' not in session:
        return redirect(url_for('login_register'))
        
    users = load_users()
    user_list = [{'nome': name, **data} for name, data in users.items()]
    sorted_users = sorted(user_list, key=lambda x: x['pontuacao'], reverse=True)
    return render_template('ranking.html', users=sorted_users)

@app.route('/usuario/<username>')
def ver_usuario(username):
    if 'username' not in session:
        return redirect(url_for('login_register'))
    
    users = load_users()
    user_data = users.get(username)
    
    if not user_data:
        flash("Usuário não encontrado! 😅", "error")
        return redirect(url_for('ranking'))
    
    # Calcula ranking
    sorted_users = sorted(users.values(), key=lambda x: x['pontuacao'], reverse=True)
    user_rank = -1
    for i, u_data in enumerate(sorted_users):
        for name, data in users.items():
            if data == u_data and name == username:
                user_rank = i + 1
                break
        if user_rank != -1:
            break
    
    achievements = get_achievements()
    user_achievements = {key: achievements[key] for key in user_data.get('achievements', []) if key in achievements}
    
    return render_template('usuario.html', user=user_data, rank=user_rank, username=username, achievements=user_achievements)

@app.route('/live-ranking')
def live_ranking():
    users = load_users()
    user_list = [{'nome': name, **data} for name, data in users.items()]
    sorted_users = sorted(user_list, key=lambda x: x['pontuacao'], reverse=True)[:100]
    return render_template('live_ranking.html', users=sorted_users)

@app.route('/jogar')
def jogar():
    if 'username' not in session:
        return redirect(url_for('login_register'))
    
    users = load_users()
    user_data = users.get(session['username'], {})
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
    
    users = load_users()
    user_data = users[session['username']]
    current_combo = session.get('combo', 0)
    
    # Adiciona à lista de respondidas
    answered_questions = user_data.get('answered_questions', [])
    if question_id not in answered_questions:
        answered_questions.append(question_id)
        user_data['answered_questions'] = answered_questions
    
    new_achievements = []
    
    if is_correct:
        # Adiciona à lista de acertadas
        correct_questions = user_data.get('correct_questions', [])
        if question_id not in correct_questions:
            correct_questions.append(question_id)
            user_data['correct_questions'] = correct_questions
        
        # Aumenta combo
        current_combo += 1
        session['combo'] = current_combo
        user_data['combo'] = current_combo
        
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
        
    else:
        # Reset combo
        session['combo'] = 0
        user_data['combo'] = 0
    
    users[session['username']] = user_data
    save_users(users)
    
    session['new_achievements'] = new_achievements

    correct_option_text = question['opcoes'][question['resposta_correta']]
    
    return render_template('resultado.html', 
                           is_correct=is_correct, 
                           correct_answer=correct_option_text,
                           question=question,
                           new_achievements=new_achievements)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
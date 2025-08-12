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
    return questions

ALL_QUESTIONS = load_questions()

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

            users[username] = {'senha': password, 'turma': turma, 'pontuacao': 0}
            save_users(users)
            session['username'] = username
            flash(f"Bem-vindo(a), {username}! Cadastro realizado com sucesso.", "success")
            return redirect(url_for('perfil'))

        elif action == 'login':
            user = users.get(username)
            if user and user['senha'] == password:
                session['username'] = username
                session.pop('answered_ids', None)
                return redirect(url_for('perfil'))
            else:
                flash("Nome de usuário ou senha incorretos.", "error")
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

    if request.method == 'POST':
        user_data['turma'] = request.form.get('turma', user_data['turma'])
        nova_senha = request.form.get('senha')
        if nova_senha:
            user_data['senha'] = nova_senha
        
        users[username] = user_data
        save_users(users)
        flash("Perfil atualizado com sucesso!", "success")
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

    return render_template('perfil.html', user=user_data, rank=user_rank, username=username)

@app.route('/ranking')
def ranking():
    if 'username' not in session:
        return redirect(url_for('login_register'))
        
    users = load_users()
    user_list = [{'nome': name, **data} for name, data in users.items()]
    sorted_users = sorted(user_list, key=lambda x: x['pontuacao'], reverse=True)
    return render_template('ranking.html', users=sorted_users)

@app.route('/jogar')
def jogar():
    if 'username' not in session:
        return redirect(url_for('login_register'))
    
    answered_ids = session.get('answered_ids', [])
    unanswered_questions = [q for q in ALL_QUESTIONS if q['id'] not in answered_ids]

    if not unanswered_questions:
        flash("Parabéns! Você respondeu todas as questões!", "success")
        return redirect(url_for('perfil'))
    
    question = random.choice(unanswered_questions)
    return render_template('jogar.html', question=question)

@app.route('/responder', methods=['POST'])
def responder():
    if 'username' not in session:
        return redirect(url_for('login_register'))
        
    question_id = int(request.form['question_id'])
    user_answer = request.form.get('opcao')

    question = next((q for q in ALL_QUESTIONS if q['id'] == question_id), None)
    
    if not question:
        flash("Questão não encontrada!", "error")
        return redirect(url_for('jogar'))

    answered_ids = session.get('answered_ids', [])
    if question_id not in answered_ids:
        answered_ids.append(question_id)
        session['answered_ids'] = answered_ids

    is_correct = (user_answer == question['resposta_correta'])
    
    if is_correct:
        users = load_users()
        users[session['username']]['pontuacao'] += 10
        save_users(users)

    correct_option_text = question['opcoes'][question['resposta_correta']]
    
    return render_template('resultado.html', 
                           is_correct=is_correct, 
                           correct_answer=correct_option_text,
                           question=question)

if __name__ == '__main__':
    app.run(debug=True)
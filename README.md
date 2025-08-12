Excelente ideia! Gamificar o processo de estudo com reforçamento imediato e competição social (ranking) é uma ótima aplicação dos princípios da Análise do Comportamento.

Aqui está um programa Flask simples e completo que implementa as funcionalidades que você descreveu.

### Estrutura de Pastas

Para organizar o projeto, crie a seguinte estrutura de pastas e arquivos:

```
/QuizPsicologia
├── app.py              # Nosso código principal do Flask
├── users.json          # Arquivo para armazenar dados dos usuários
└── templates/
    ├── base.html       # Layout base para todas as páginas
    ├── login.html      # Tela de cadastro e login
    ├── perfil.html     # Tela 'Minha Pontuação' e edição de perfil
    ├── ranking.html    # Tela com o ranking dos alunos
    ├── jogar.html      # Tela para responder a uma pergunta
    └── resultado.html  # Tela que mostra se a resposta foi correta ou não
```

---

### 1. O Código Principal (`app.py`)

Este é o coração da nossa aplicação. Ele gerencia as rotas, a lógica do jogo, os usuários e as pontuações.

```python
import json
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash

# --- Configuração Inicial do Flask ---
app = Flask(__name__)
# Chave secreta é necessária para usar 'session' e 'flash'
app.secret_key = 'super_secret_key_change_this'

# --- Carregando as Questões ---
# (Cole o JSON que geramos anteriormente aqui)
QUESTIONS_DATA = {
  "capitulo_1": [
    { "pergunta": "De acordo com a Análise do Comportamento, o que é um 'Estímulo' (S)?", "opcoes": { "a": "Uma mudança no organismo.", "b": "Uma parte ou uma mudança em uma parte do ambiente.", "c": "A relação entre o ambiente e o organismo.", "d": "Um comportamento involuntário." }, "resposta_correta": "b" },
    { "pergunta": "Como é definida uma 'Resposta' (R) no contexto do comportamento reflexo?", "opcoes": { "a": "Uma mudança no ambiente causada pelo organismo.", "b": "A causa de um comportamento.", "c": "Uma mudança no organismo.", "d": "Uma ação voluntária e consciente." }, "resposta_correta": "c" },
    { "pergunta": "Qual lei do reflexo estabelece que a intensidade do estímulo é diretamente proporcional à magnitude da resposta?", "opcoes": { "a": "Lei do Limiar", "b": "Lei da Latência", "c": "Lei da Intensidade e Magnitude", "d": "Lei da Habituação" }, "resposta_correta": "c" },
    { "pergunta": "O que é 'Habituação'?", "opcoes": { "a": "Um aumento na magnitude da resposta quando um estímulo é apresentado repetidamente.", "b": "Um decréscimo na magnitude da resposta quando um estímulo é apresentado repetidamente.", "c": "O tempo que leva para uma resposta ocorrer.", "d": "O aprendizado de um novo reflexo." }, "resposta_correta": "b" },
    { "pergunta": "Qual é a relação entre os reflexos inatos e as emoções, segundo o material?", "opcoes": { "a": "As emoções são comportamentos completamente voluntários e não têm relação com reflexos.", "b": "Muitas das emoções que sentimos são parte de comportamentos reflexos.", "c": "Reflexos e emoções são a mesma coisa.", "d": "As emoções controlam os reflexos, mas não o contrário." }, "resposta_correta": "b" }
  ],
  "capitulo_2": [
    { "pergunta": "No experimento clássico de Pavlov, o som da sineta, antes de qualquer condicionamento, era considerado um:", "opcoes": { "a": "Estímulo Incondicionado (US)", "b": "Estímulo Neutro (NS)", "c": "Estímulo Condicionado (CS)", "d": "Resposta Condicionada (CR)" }, "resposta_correta": "b" },
    { "pergunta": "No caso do 'pequeno Albert' de John Watson, após o condicionamento, o rato branco tornou-se um:", "opcoes": { "a": "Estímulo incondicionado (US)", "b": "Estímulo neutro (NS)", "c": "Estímulo condicionado (CS)", "d": "Resposta incondicionada (UR)" }, "resposta_correta": "c" },
    { "pergunta": "Uma pessoa que desenvolveu medo de abelhas após uma picada e passa a ter medo também de vespas está demonstrando o fenômeno de:", "opcoes": { "a": "Recuperação espontânea", "b": "Extinção respondente", "c": "Condicionamento de ordem superior", "d": "Generalização respondente" }, "resposta_correta": "d" },
    { "pergunta": "Qual procedimento consiste em apresentar o CS repetidas vezes sem o US para que a CR desapareça?", "opcoes": { "a": "Extinção respondente", "b": "Contracondicionamento", "c": "Dessensibilização sistemática", "d": "Recuperação espontânea" }, "resposta_correta": "a" },
    { "pergunta": "A técnica terapêutica que consiste em condicionar uma resposta contrária (ex: relaxamento) àquela produzida por um CS (ex: ansiedade) é chamada de:", "opcoes": { "a": "Generalização", "b": "Extinção", "c": "Contracondicionamento", "d": "Condicionamento de ordem superior" }, "resposta_correta": "c" }
  ]
}

# Combina todas as questões e adiciona um ID único a cada uma
ALL_QUESTIONS = []
question_id_counter = 0
for chapter, questions in QUESTIONS_DATA.items():
    for q in questions:
        q['id'] = question_id_counter
        ALL_QUESTIONS.append(q)
        question_id_counter += 1

# --- Funções Auxiliares para Gerenciar Usuários ---
def load_users():
    """Carrega os dados dos usuários do arquivo JSON."""
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(users):
    """Salva os dados dos usuários no arquivo JSON."""
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

# --- Rotas da Aplicação ---

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
                # Limpa as questões respondidas de sessões anteriores
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
        # Lógica para editar perfil
        user_data['turma'] = request.form.get('turma', user_data['turma'])
        nova_senha = request.form.get('senha')
        if nova_senha:
            user_data['senha'] = nova_senha
        
        users[username] = user_data
        save_users(users)
        flash("Perfil atualizado com sucesso!", "success")
        return redirect(url_for('perfil'))

    # Calcula o ranking do usuário
    sorted_users = sorted(users.values(), key=lambda x: x['pontuacao'], reverse=True)
    user_rank = -1
    # Precisamos encontrar o nome do usuário para comparar
    for i, u_data in enumerate(sorted_users):
        # A chave do dicionário (nome) não está nos valores, então precisamos iterar sobre o dicionário original
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
    # Adiciona o nome ao dicionário de dados para facilitar a exibição no template
    user_list = [{'nome': name, **data} for name, data in users.items()]
    # Ordena por pontuação
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

    # Adiciona à lista de respondidas na sessão
    answered_ids = session.get('answered_ids', [])
    if question_id not in answered_ids:
        answered_ids.append(question_id)
        session['answered_ids'] = answered_ids

    is_correct = (user_answer == question['resposta_correta'])
    
    # Reforçamento!
    if is_correct:
        users = load_users()
        users[session['username']]['pontuacao'] += 10 # Adiciona 10 pontos por acerto
        save_users(users)

    correct_option_text = question['opcoes'][question['resposta_correta']]
    
    return render_template('resultado.html', 
                           is_correct=is_correct, 
                           correct_answer=correct_option_text,
                           question=question)

if __name__ == '__main__':
    app.run(debug=True)
```

---

### 2. Os Templates (Arquivos HTML)

Coloque estes arquivos dentro da pasta `templates`.

#### `base.html`
Este é o esqueleto da nossa aplicação. Todas as outras páginas herdarão dele.

```html
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quiz de Análise do Comportamento</title>
    <style>
        body { font-family: sans-serif; background-color: #f0f2f5; color: #333; margin: 0; padding: 0; }
        .container { max-width: 800px; margin: 2em auto; padding: 2em; background-color: #fff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        nav { background-color: #001f5b; padding: 1em; }
        nav a { color: white; text-decoration: none; margin-right: 1.5em; font-weight: bold; }
        nav a:hover { text-decoration: underline; }
        h1, h2 { color: #001f5b; }
        .flash { padding: 1em; margin-bottom: 1em; border-radius: 4px; }
        .flash.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .flash.error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .flash.info { background-color: #cce5ff; color: #004085; border: 1px solid #b8daff; }
        .btn { background-color: #003399; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; font-size: 16px; }
        .btn:hover { background-color: #002266; }
    </style>
</head>
<body>
    <nav>
        {% if session.username %}
            <a href="{{ url_for('perfil') }}">Minha Pontuação</a>
            <a href="{{ url_for('ranking') }}">Ranking</a>
            <a href="{{ url_for('jogar') }}">Jogar</a>
            <a href="{{ url_for('logout') }}">Sair</a>
        {% endif %}
    </nav>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
```

#### `login.html`

```html
{% extends "base.html" %}
{% block content %}
    <h1>Bem-vindo ao Quiz de Análise do Comportamento!</h1>
    <p>Faça seu cadastro para começar a jogar ou entre com seus dados.</p>

    <div style="display: flex; justify-content: space-around;">
        
        <!-- Formulário de Cadastro -->
        <form action="/" method="post" style="width: 45%;">
            <h2>Cadastre-se</h2>
            <label for="reg_nome">Nome:</label><br>
            <input type="text" id="reg_nome" name="nome" required><br><br>
            
            <label for="turma">Turma:</label><br>
            <input type="text" id="turma" name="turma" required><br><br>
            
            <label for="reg_senha">Senha:</label><br>
            <input type="password" id="reg_senha" name="senha" required><br><br>
            
            <button type="submit" name="action" value="register" class="btn">Cadastrar e Jogar</button>
        </form>

        <!-- Formulário de Login -->
        <form action="/" method="post" style="width: 45%;">
            <h2>Login</h2>
            <label for="login_nome">Nome:</label><br>
            <input type="text" id="login_nome" name="nome" required><br><br>
            
            <label for="login_senha">Senha:</label><br>
            <input type="password" id="login_senha" name="senha" required><br><br>

            <button type="submit" name="action" value="login" class="btn">Entrar</button>
        </form>
    </div>
{% endblock %}
```

#### `perfil.html`

```html
{% extends "base.html" %}
{% block content %}
    <h1>Perfil de {{ username }}</h1>
    
    <h2>Sua Pontuação</h2>
    <p><strong>Pontos:</strong> {{ user.pontuacao }}</p>
    <p><strong>Posição no Ranking:</strong> {{ rank }}º</p>
    <p><strong>Turma:</strong> {{ user.turma }}</p>

    <hr>

    <h2>Editar Perfil</h2>
    <form action="{{ url_for('perfil') }}" method="post">
        <label for="turma">Mudar Turma:</label><br>
        <input type="text" name="turma" id="turma" value="{{ user.turma }}"><br><br>

        <label for="senha">Nova Senha (deixe em branco para não alterar):</label><br>
        <input type="password" name="senha" id="senha"><br><br>
        
        <button type="submit" class="btn">Salvar Alterações</button>
    </form>
{% endblock %}
```

#### `ranking.html`

```html
{% extends "base.html" %}
{% block content %}
    <h1>Ranking Geral</h1>
    <ol>
        {% for user in users %}
            <li>
                <strong>{{ user.nome }}</strong> (Turma: {{ user.turma }}) - {{ user.pontuacao }} pontos
            </li>
        {% else %}
            <li>Nenhum jogador no ranking ainda.</li>
        {% endfor %}
    </ol>
{% endblock %}
```

#### `jogar.html`

```html
{% extends "base.html" %}
{% block content %}
    <h1>Pergunta!</h1>
    <h2>{{ question.pergunta }}</h2>

    <form action="{{ url_for('responder') }}" method="post">
        <input type="hidden" name="question_id" value="{{ question.id }}">
        
        {% for key, value in question.opcoes.items() %}
            <p>
                <input type="radio" id="opcao_{{ key }}" name="opcao" value="{{ key }}" required>
                <label for="opcao_{{ key }}">{{ value }}</label>
            </p>
        {% endfor %}
        
        <button type="submit" class="btn">Responder</button>
    </form>
{% endblock %}
```

#### `resultado.html`

```html
{% extends "base.html" %}
{% block content %}
    {% if is_correct %}
        <h1 style="color: green;">Parabéns, você acertou!</h1>
        <p><strong>Reforço Positivo:</strong> +10 pontos foram adicionados à sua pontuação!</p>
    {% else %}
        <h1 style="color: red;">Resposta Incorreta!</h1>
        <p>A resposta correta para a pergunta <em>"{{ question.pergunta }}"</em> era:</p>
        <p><strong>{{ correct_answer }}</strong></p>
        <p>Não desanime! O erro faz parte do aprendizado. 😉</p>
    {% endif %}
    
    <br>
    <a href="{{ url_for('jogar') }}" class="btn">Próxima Pergunta &rarr;</a>
{% endblock %}
```

---

### Como Executar o Programa

1.  **Instale o Flask:**
    ```bash
    pip install Flask
    ```

2.  **Salve os arquivos:** Crie a estrutura de pastas e salve cada trecho de código no arquivo correspondente.

3.  **Execute o servidor:** Abra o terminal na pasta `QuizPsicologia` e execute o comando:
    ```bash
    python app.py
    ```

4.  **Acesse no navegador:** Abra seu navegador e vá para `http://127.0.0.1:5000`. Você verá a tela de cadastro e login.

### Elementos de Gamificação e Reforçamento

*   **Reforçamento Imediato:** A tela `resultado.html` aparece logo após a resposta, informando se o aluno acertou ou errou.
*   **Reforçador Positivo:** A mensagem "Parabéns, você acertou!" e a adição de "+10 pontos" servem como reforçadores positivos para a resposta correta.
*   **Punição Negativa (Leve):** A mensagem de erro e a não obtenção de pontos funcionam como uma leve punição (não ganhar o reforçador). A mensagem é amigável para não ser aversiva.
*   **Reforçador Social (Ranking):** A tela de ranking cria uma competição saudável e serve como um reforçador social, onde os alunos podem ver seu progresso em relação aos outros.
*   **Contingência Clara:** A regra é simples e clara: responda corretamente (comportamento) e ganhe pontos (consequência reforçadora).
*   **Esquema de Reforçamento:** Como as perguntas são aleatórias, o "prêmio" (uma pergunta fácil ou um tópico que o aluno domina) aparece em um **Esquema de Razão Variável (VR)**, o que é altamente eficaz para manter o engajamento. Cada resposta correta é reforçada (pontos), o que se assemelha a um **Esquema de Reforçamento Contínuo (CRF)** para a "ação de acertar", o que é ideal para a aquisição e manutenção do comportamento de estudar.
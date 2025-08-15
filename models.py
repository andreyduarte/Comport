from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    username = db.Column(db.String(50), primary_key=True)
    senha = db.Column(db.String(255), nullable=False)
    turma = db.Column(db.String(100), nullable=False)
    pontuacao = db.Column(db.Integer, default=0)
    combo = db.Column(db.Integer, default=0)
    max_combo = db.Column(db.Integer, default=0)
    is_teacher = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    questions = db.relationship('UserQuestion', backref='user', lazy=True, cascade='all, delete-orphan')
    achievements = db.relationship('UserAchievement', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'username': self.username,
            'senha': self.senha,
            'turma': self.turma,
            'pontuacao': self.pontuacao,
            'combo': self.combo,
            'max_combo': self.max_combo,
            'is_teacher': self.is_teacher,
            'answered_questions': [q.question_id for q in self.questions],
            'correct_questions': [q.question_id for q in self.questions if q.is_correct],
            'achievements': [a.achievement_key for a in self.achievements]
        }

class UserQuestion(db.Model):
    __tablename__ = 'user_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), db.ForeignKey('users.username'), nullable=False)
    question_id = db.Column(db.Integer, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    
    __table_args__ = (UniqueConstraint('username', 'question_id', name='unique_user_question'),)

class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), db.ForeignKey('users.username'), nullable=False)
    achievement_key = db.Column(db.String(50), nullable=False)
    
    __table_args__ = (UniqueConstraint('username', 'achievement_key', name='unique_user_achievement'),)

class AdminLog(db.Model):
    __tablename__ = 'admin_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_username = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    target_username = db.Column(db.String(50), nullable=True)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False)
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from sqlalchemy import or_

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_master.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

#--------------------------------------- Models----------------------------------------------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(100))
    dob = db.Column(db.Date)
    is_admin = db.Column(db.Boolean, default=False)
    quiz_scores = db.relationship('Score', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    chapters = db.relationship('Chapter', backref='subject', lazy=True, cascade='all, delete-orphan')

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    quizzes = db.relationship('Quiz', backref='chapter', lazy=True, cascade='all, delete-orphan')

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)  # When quiz becomes available
    end_date = db.Column(db.DateTime, nullable=False)    # When quiz expires
    duration = db.Column(db.Integer)  # Duration in minutes
    remarks = db.Column(db.Text)
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade='all, delete-orphan')
    scores = db.relationship('Score', backref='quiz', lazy=True, cascade='all, delete-orphan')


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_1 = db.Column(db.String(200), nullable=False)
    option_2 = db.Column(db.String(200), nullable=False)
    option_3 = db.Column(db.String(200), nullable=False)
    option_4 = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    attempt_date = db.Column(db.DateTime, default=datetime.now)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_admin():
    with app.app_context():
        admin = User.query.filter_by(email='admin@quizmaster.com').first()
        if not admin:
            admin = User(
                email='admin@quizmaster.com',
                full_name='Quiz Master Admin',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

#---------------------------- Routes------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        qualification = request.form.get('qualification')
        dob = datetime.strptime(request.form.get('dob'), '%Y-%m-%d')

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        user = User(
            email=email,
            full_name=full_name,
            qualification=qualification,
            dob=dob
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

#------------------------------------- Admin routes--------------------------------------------
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    subjects = Subject.query.all()
    users = User.query.filter_by(is_admin=False).all()
    quizzes = Quiz.query.all()
    return render_template('admin/dashboard.html', subjects=subjects, users=users, quizzes=quizzes)

@app.route('/admin/subjects', methods=['GET', 'POST'])
@login_required
def manage_subjects():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        subject = Subject(name=name, description=description)
        db.session.add(subject)
        db.session.commit()
        flash('Subject added successfully')
        return redirect(url_for('manage_subjects'))
    
    subjects = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects)

@app.route('/admin/subjects/<int:subject_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    subject = Subject.query.get_or_404(subject_id)
    if request.method == 'POST':
        subject.name = request.form.get('name')
        subject.description = request.form.get('description')
        db.session.commit()
        flash('Subject updated successfully')
        return redirect(url_for('manage_subjects'))
    
    return render_template('admin/edit_subject.html', subject=subject)

@app.route('/admin/subjects/<int:subject_id>/delete')
@login_required
def delete_subject(subject_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully')
    return redirect(url_for('manage_subjects'))

@app.route('/admin/chapters', methods=['GET', 'POST'])
@login_required
def manage_chapters():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        subject_id = request.form.get('subject_id')
        chapter = Chapter(name=name, description=description, subject_id=subject_id)
        db.session.add(chapter)
        db.session.commit()
        flash('Chapter added successfully')
        return redirect(url_for('manage_chapters'))
    
    chapters = Chapter.query.all()
    subjects = Subject.query.all()
    return render_template('admin/chapters.html', chapters=chapters, subjects=subjects)

@app.route('/admin/chapters/<int:chapter_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_chapter(chapter_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    chapter = Chapter.query.get_or_404(chapter_id)
    if request.method == 'POST':
        chapter.name = request.form.get('name')
        chapter.description = request.form.get('description')
        chapter.subject_id = request.form.get('subject_id')
        db.session.commit()
        flash('Chapter updated successfully')
        return redirect(url_for('manage_chapters'))
    
    subjects = Subject.query.all()
    return render_template('admin/edit_chapter.html', chapter=chapter, subjects=subjects)

@app.route('/admin/chapters/<int:chapter_id>/delete')
@login_required
def delete_chapter(chapter_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    chapter = Chapter.query.get_or_404(chapter_id)
    try:
        db.session.delete(chapter)
        db.session.commit()
        flash('Chapter deleted successfully')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting chapter: ' + str(e))
    return redirect(url_for('manage_chapters'))

@app.route('/admin/quizzes', methods=['GET', 'POST'])
@login_required
def manage_quizzes():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        chapter_id = request.form.get('chapter_id')
        start_date_str = request.form.get('start_date')
        start_time_str = request.form.get('start_time')
        end_date_str = request.form.get('end_date')
        end_time_str = request.form.get('end_time')
        duration = request.form.get('duration')
        remarks = request.form.get('remarks')
        
        
        start_datetime = datetime.strptime(f"{start_date_str} {start_time_str}", '%Y-%m-%d %H:%M')
        end_datetime = datetime.strptime(f"{end_date_str} {end_time_str}", '%Y-%m-%d %H:%M')
        
        
        if start_datetime >= end_datetime:
            flash("Start date/time must be before end date/time.")
            return redirect(url_for('manage_quizzes'))
        
        quiz = Quiz(
            title=title,
            chapter_id=chapter_id,
            start_date=start_datetime,
            end_date=end_datetime,
            duration=duration,
            remarks=remarks
        )
        db.session.add(quiz)
        db.session.commit()
        flash('Quiz added successfully')
        return redirect(url_for('edit_quiz_questions', quiz_id=quiz.id))
    
    quizzes = Quiz.query.all()
    chapters = Chapter.query.all()
    return render_template('admin/quizzes.html', quizzes=quizzes, chapters=chapters)


@app.route('/admin/quizzes/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == 'POST':
        quiz.title = request.form.get('title')
        quiz.chapter_id = request.form.get('chapter_id')
        date_str = request.form.get('date_of_quiz')
        time_str = request.form.get('time_of_quiz')
        quiz.date_of_quiz = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
        quiz.duration = request.form.get('duration')
        quiz.remarks = request.form.get('remarks')
        db.session.commit()
        flash('Quiz updated successfully')
        return redirect(url_for('manage_quizzes'))
    
    chapters = Chapter.query.all()
    return render_template('admin/edit_quiz.html', quiz=quiz, chapters=chapters)

@app.route('/admin/quizzes/<int:quiz_id>/delete')
@login_required
def delete_quiz(quiz_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted successfully')
    return redirect(url_for('manage_quizzes'))

@app.route('/admin/quizzes/<int:quiz_id>/questions', methods=['GET', 'POST'])
@login_required
def edit_quiz_questions(quiz_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if request.method == 'POST':
        question_text = request.form.get('question_text')
        option_1 = request.form.get('option_1')
        option_2 = request.form.get('option_2')
        option_3 = request.form.get('option_3')
        option_4 = request.form.get('option_4')
        correct_option = request.form.get('correct_option')
        
        question = Question(
            quiz_id=quiz.id,
            question_text=question_text,
            option_1=option_1,
            option_2=option_2,
            option_3=option_3,
            option_4=option_4,
            correct_option=int(correct_option)
        )
        db.session.add(question)
        db.session.commit()
        flash('Question added successfully')
        return redirect(url_for('edit_quiz_questions', quiz_id=quiz.id))
    
    return render_template('admin/edit_quiz_questions.html', quiz=quiz)

@app.route('/admin/questions/<int:question_id>/delete')
@login_required
def delete_question(question_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully')
    return redirect(url_for('edit_quiz_questions', quiz_id=quiz_id))

@app.route('/admin/users')
@login_required
def view_users():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/view_users.html', users=users)

@app.route('/admin/search', methods=['GET'])
@login_required
def admin_search():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    query = request.args.get('q', '')
    user_results = []
    subject_results = []
    quiz_results = []
    
    if query:
        # Search non-admin users by full name or email.
        user_results = User.query.filter(
            User.is_admin == False,
            or_(
                User.full_name.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%')
            )
        ).all()
        
        # Search subjects by name or description.
        subject_results = Subject.query.filter(
            or_(
                Subject.name.ilike(f'%{query}%'),
                Subject.description.ilike(f'%{query}%')
            )
        ).all()
        
        # Search quizzes by title.
        quiz_results = Quiz.query.filter(
            Quiz.title.ilike(f'%{query}%')
        ).all()
    
    return render_template('admin/search_results.html', 
                           query=query,
                           user_results=user_results, 
                           subject_results=subject_results, 
                           quiz_results=quiz_results)


#---------------------------------------- User routes------------------------------------------------
@app.route('/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    
    available_quizzes = Quiz.query.all()
    completed_quizzes = Score.query.filter_by(user_id=current_user.id).order_by(Score.attempt_date.desc()).all()
    
    return render_template('user/dashboard.html', 
                           available_quizzes=available_quizzes,
                           completed_quizzes=completed_quizzes)


@app.route('/quizzes')
@login_required
def available_quizzes():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    
    quizzes = Quiz.query.all()
    return render_template('user/available_quizzes.html', quizzes=quizzes)



@app.route('/quiz/<int:quiz_id>')
@login_required
def take_quiz(quiz_id):
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    now = datetime.now()
    
    print(f"Current time: {now}")
    print(f"Quiz start date: {quiz.start_date}, end date: {quiz.end_date}")

    if now < quiz.start_date:
        flash('This quiz is not yet available. Please try later.')
        return redirect(url_for('available_quizzes'))
    elif now > quiz.end_date:
        flash('This quiz has expired.')
        return redirect(url_for('available_quizzes'))
    
    return render_template('user/take_quiz.html', quiz=quiz)



@app.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    total_questions = len(quiz.questions)
    correct_answers = 0
    
    for question in quiz.questions:
        user_answer = request.form.get(f'question_{question.id}')
        if user_answer and int(user_answer) == question.correct_option:
            correct_answers += 1
    
    score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    score = Score(
        quiz_id=quiz.id,
        user_id=current_user.id,
        score=score_percentage
    )
    db.session.add(score)
    db.session.commit()
    
    flash(f'Quiz submitted successfully! Your score: {score_percentage:.2f}%')
    return redirect(url_for('user_dashboard'))

@app.route('/profile')
@login_required
def profile():
    return render_template('user/profile.html')

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.qualification = request.form.get('qualification')
        if request.form.get('password'):
            current_user.set_password(request.form.get('password'))
        db.session.commit()
        flash('Profile updated successfully')
        return redirect(url_for('profile'))
    
    return render_template('user/edit_profile.html')

# API Routes
@app.route('/api/subjects', methods=['GET'])
def api_subjects():
    subjects = Subject.query.all()
    return jsonify([{
        'id': subject.id,
        'name': subject.name,
        'description': subject.description
    } for subject in subjects])

@app.route('/api/chapters/<int:subject_id>', methods=['GET'])
def api_chapters(subject_id):
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return jsonify([{
        'id': chapter.id,
        'name': chapter.name,
        'description': chapter.description
    } for chapter in chapters])

@app.route('/api/quizzes/<int:chapter_id>', methods=['GET'])
def api_quizzes(chapter_id):
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return jsonify([{
        'id': quiz.id,
        'title': quiz.title,
        'date_of_quiz': quiz.date_of_quiz.isoformat(),
        'duration': quiz.duration
    } for quiz in quizzes])

@app.route('/scores')
@login_required
def view_scores():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    

    scores = Score.query.filter_by(user_id=current_user.id).order_by(Score.attempt_date.desc()).all()
    return render_template('user/scores.html', scores=scores)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin()
    app.run(debug=True)
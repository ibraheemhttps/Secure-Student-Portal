from flask import Flask, render_template, redirect, url_for, request, flash
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import bcrypt
import logging

# ─── App Setup ─────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_123'
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'portal.db') 

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ─── Logging Setup ─────────────────────────────────────────
logging.basicConfig(
    filename='portal.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('portal')

# ─── Models ────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id             = db.Column(db.Integer, primary_key=True)
    username       = db.Column(db.String(150), unique=True, nullable=False)
    password       = db.Column(db.String(200), nullable=False)
    role           = db.Column(db.String(20), nullable=False, default='student')
    failed_attempts = db.Column(db.Integer, default=0)
    is_locked      = db.Column(db.Boolean, default=False)
    marks          = db.relationship('Mark', backref='student', lazy=True)

class Mark(db.Model):
    __tablename__ = 'marks'
    id         = db.Column(db.Integer, primary_key=True)
    subject    = db.Column(db.String(100), nullable=False)
    marks      = db.Column(db.Integer, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

with app.app_context():
    db.create_all()

# ─── User Loader ───────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ──────────────────────────────────────────────────────────
#  AUTH ROUTES
# ──────────────────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        role     = request.form.get('role', 'student')

        if not username or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken.', 'danger')
            return redirect(url_for('register'))

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        new_user  = User(
            username=username,
            password=hashed_pw.decode('utf-8'),
            role=role
        )
        db.session.add(new_user)
        db.session.commit()

        logger.info(f'New user registered: {username} as {role}')
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()

        if not username or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()

        # Check if account is locked
        if user and user.is_locked:
            logger.warning(f'Locked account login attempt: {username}')
            flash('🔒 Account is locked due to too many failed attempts. Contact admin.', 'danger')
            return redirect(url_for('login'))

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            # Reset failed attempts on successful login
            user.failed_attempts = 0
            user.is_locked       = False
            db.session.commit()

            login_user(user)
            logger.info(f'Successful login: {username} ({user.role})')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            # Wrong password — increment failed attempts
            if user:
                user.failed_attempts += 1
                logger.warning(f'Failed login attempt {user.failed_attempts}/5 for: {username}')

                if user.failed_attempts >= 5:
                    user.is_locked = True
                    db.session.commit()
                    logger.warning(f'Account LOCKED: {username}')
                    flash('🔒 Account locked after 5 failed attempts. Contact admin.', 'danger')
                    return redirect(url_for('login'))

                db.session.commit()
                remaining = 5 - user.failed_attempts
                flash(f'Invalid password. {remaining} attempts remaining before lockout.', 'danger')
            else:
                logger.warning(f'Failed login attempt for unknown user: {username}')
                flash('Invalid username or password.', 'danger')

            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logger.info(f'User {current_user.username} logged out')
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ──────────────────────────────────────────────────────────
#  STUDENT ROUTES
# ──────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_dashboard'))

    marks   = Mark.query.filter_by(student_id=current_user.id).all()
    average = round(sum(m.marks for m in marks) / len(marks), 2) if marks else 0

    logger.info(f'Student {current_user.username} viewed dashboard')
    return render_template('student_dashboard.html',
                           user=current_user,
                           marks=marks,
                           average=average)


# ──────────────────────────────────────────────────────────
#  ADMIN ROUTES
# ──────────────────────────────────────────────────────────

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('student_dashboard'))

    students = User.query.filter_by(role='student').all()
    logger.info(f'Admin {current_user.username} viewed admin dashboard')
    return render_template('admin_dashboard.html', students=students)


@app.route('/admin/student/<int:student_id>')
@login_required
def view_student(student_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('student_dashboard'))

    student = User.query.get_or_404(student_id)
    marks   = Mark.query.filter_by(student_id=student_id).all()
    return render_template('view_student.html', student=student, marks=marks)


@app.route('/admin/add_mark/<int:student_id>', methods=['POST'])
@login_required
def add_mark(student_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('student_dashboard'))

    subject    = request.form.get('subject').strip()
    marks_val  = request.form.get('marks').strip()

    if not subject or not marks_val:
        flash('All fields are required.', 'danger')
        return redirect(url_for('view_student', student_id=student_id))

    if not marks_val.isdigit() or not (0 <= int(marks_val) <= 100):
        flash('Marks must be a number between 0 and 100.', 'danger')
        return redirect(url_for('view_student', student_id=student_id))

    new_mark = Mark(
        subject=subject,
        marks=int(marks_val),
        student_id=student_id
    )
    db.session.add(new_mark)
    db.session.commit()

    logger.info(f'Admin {current_user.username} added mark for student_id {student_id}: {subject} = {marks_val}')
    flash('Marks added successfully!', 'success')
    return redirect(url_for('view_student', student_id=student_id))


@app.route('/admin/delete_mark/<int:mark_id>/<int:student_id>', methods=['POST'])
@login_required
def delete_mark(mark_id, student_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('student_dashboard'))

    mark = Mark.query.get_or_404(mark_id)
    db.session.delete(mark)
    db.session.commit()

    logger.info(f'Admin {current_user.username} deleted mark_id {mark_id}')
    flash('Mark deleted.', 'warning')
    return redirect(url_for('view_student', student_id=student_id))

@app.route('/admin/unlock/<int:user_id>', methods=['POST'])
@login_required
def unlock_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('student_dashboard'))

    user = User.query.get_or_404(user_id)
    user.is_locked       = False
    user.failed_attempts = 0
    db.session.commit()

    logger.info(f'Admin {current_user.username} unlocked account: {user.username}')
    flash(f'Account {user.username} has been unlocked.', 'success')
    return redirect(url_for('admin_dashboard'))

# ─── CSRF Error Handler ────────────────────────────────────
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    logger.warning(f'CSRF attack blocked: {e.description}')
    flash('⚠️ Security error: Invalid or missing CSRF token. Request blocked.', 'danger')
    return redirect(url_for('login'))
# ──────────────────────────────────────────────────────────
#  RUN
# ──────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)
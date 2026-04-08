from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'tasks.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

CATEGORIES = ['Work', 'Personal', 'Health', 'Learning', 'Other']
PRIORITIES = ['Low', 'Medium', 'High']

class Task(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    title     = db.Column(db.String(200), nullable=False)
    category  = db.Column(db.String(50), default='Other')
    priority  = db.Column(db.String(20), default='Medium')
    due_date  = db.Column(db.Date, nullable=True)
    done      = db.Column(db.Boolean, default=False)
    created   = db.Column(db.DateTime, default=datetime.utcnow)
    notes     = db.Column(db.Text, default='')

    def to_dict(self):
        return {
            'id':       self.id,
            'title':    self.title,
            'category': self.category,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'done':     self.done,
            'notes':    self.notes,
        }


@app.route('/')
def index():
    today        = date.today()
    filter_cat   = request.args.get('category', 'All')
    filter_pri   = request.args.get('priority', 'All')
    filter_done  = request.args.get('done', 'All')

    query = Task.query

    if filter_cat != 'All':
        query = query.filter_by(category=filter_cat)
    if filter_pri != 'All':
        query = query.filter_by(priority=filter_pri)
    if filter_done == 'Done':
        query = query.filter_by(done=True)
    elif filter_done == 'Pending':
        query = query.filter_by(done=False)

    tasks         = query.order_by(Task.created.desc()).all()
    total         = Task.query.count()
    completed     = Task.query.filter_by(done=True).count()
    pending       = total - completed
    today_tasks   = Task.query.filter(Task.due_date == today).count()

    return render_template(
        'index.html',
        tasks=tasks,
        today=today.isoformat(),
        total=total,
        completed=completed,
        pending=pending,
        today_tasks=today_tasks,
        categories=CATEGORIES,
        priorities=PRIORITIES,
        filter_cat=filter_cat,
        filter_pri=filter_pri,
        filter_done=filter_done,
    )


@app.route('/add', methods=['POST'])
def add_task():
    title     = request.form.get('title', '').strip()
    category  = request.form.get('category', 'Other')
    priority  = request.form.get('priority', 'Medium')
    notes     = request.form.get('notes', '').strip()
    due_str   = request.form.get('due_date', '')

    if not title:
        return redirect(url_for('index'))

    due = None
    if due_str:
        try:
            due = datetime.strptime(due_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    task = Task(title=title, category=category, priority=priority, due_date=due, notes=notes)
    db.session.add(task)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/toggle/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.done = not task.done
    db.session.commit()
    return jsonify({'done': task.done})


@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/edit/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    task     = Task.query.get_or_404(task_id)
    data     = request.get_json()
    task.title    = data.get('title', task.title).strip()
    task.category = data.get('category', task.category)
    task.priority = data.get('priority', task.priority)
    task.notes    = data.get('notes', task.notes)
    due_str       = data.get('due_date', '')
    if due_str:
        try:
            task.due_date = datetime.strptime(due_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    else:
        task.due_date = None
    db.session.commit()
    return jsonify(task.to_dict())


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0',port=5000,debug=True)

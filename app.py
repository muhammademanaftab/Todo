from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import case
from datetime import datetime, date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)


class TodoModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    desc = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.Date, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(10), nullable=False, default='Medium')  

def validate_input(input_string):
    return input_string.strip()

@app.route('/', methods=['GET', 'POST'])
def Home():
    if request.method == 'POST':
        title = validate_input(request.form.get('title'))
        desc = validate_input(request.form.get('desc'))
        due_date = request.form.get('due_date')
        priority = request.form.get('priority')

        if not title or not desc:
            flash("Both Title and Description are required.")
        else:
            due_date_obj = None
            if due_date:
                try:
                    due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                    if not (1900 <= due_date_obj.year <= 2100):
                        flash("Please enter a realistic year between 1900 and 2100.")
                        return redirect(url_for('Home'))
                    if due_date_obj < date.today():
                        flash("Due date cannot be earlier than today.")
                        return redirect(url_for('Home'))
                except ValueError:
                    flash("Invalid date format. Please enter a valid date in YYYY-MM-DD format.")
                    return redirect(url_for('Home'))
            
            todo = TodoModel(title=title, desc=desc, due_date=due_date_obj, priority=priority)
            db.session.add(todo)
            db.session.commit()
            return redirect(url_for('Home'))

    priority_order = case(
        (TodoModel.priority == 'High', 1),
        (TodoModel.priority == 'Medium', 2),
        (TodoModel.priority == 'Low', 3),
        else_=4
    )

    completed_tasks = TodoModel.query.filter_by(completed=True).order_by(priority_order, TodoModel.due_date).all()
    uncompleted_tasks = TodoModel.query.filter_by(completed=False).order_by(priority_order, TodoModel.due_date).all()
    return render_template('index.html', completed_tasks=completed_tasks, uncompleted_tasks=uncompleted_tasks, current_date=date.today())


@app.route('/today')
def today_tasks():
    today = date.today()
    today_todos = TodoModel.query.filter(TodoModel.due_date == today, TodoModel.completed == False).all()
    return render_template('today.html', today_todos=today_todos)


@app.route('/toggle_complete/<int:id>', methods=['POST'])
def toggle_complete(id):
    todo = TodoModel.query.get_or_404(id)
    todo.completed = not todo.completed
    db.session.commit()
    return redirect(url_for('Home'))


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    todo = TodoModel.query.get_or_404(id)
    if request.method == 'POST':
        title = validate_input(request.form.get('title'))
        desc = validate_input(request.form.get('desc'))
        due_date = request.form.get('due_date')

        if title and desc:
            todo.title = title
            todo.desc = desc
            if due_date:
                try:
                    due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                    todo.due_date = due_date_obj
                except ValueError:
                    flash("Invalid date format. Please enter a valid date in YYYY-MM-DD format.")
                    return redirect(url_for('update', id=id))
            else:
                todo.due_date = None
            db.session.commit()
        return redirect(url_for('Home'))
    
    return render_template('update.html', todo=todo)


@app.route('/task/<int:id>')
def task_detail(id):
    todo = TodoModel.query.get_or_404(id)
    return render_template('task_detail.html', todo=todo)


@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    todo = TodoModel.query.get(id)
    if todo:
        db.session.delete(todo)
        db.session.commit()
    return redirect(url_for('Home'))


@app.route('/search', methods=['GET'])
def search():
    search_query = request.args.get('search', '').strip()
    priority = request.args.get('priority')
    status = request.args.get('status')

    todos = TodoModel.query
    if search_query:
        todos = todos.filter(TodoModel.title.like(f"%{search_query}%"))
    if priority:
        todos = todos.filter_by(priority=priority)
    if status == 'completed':
        todos = todos.filter_by(completed=True)
    elif status == 'uncompleted':
        todos = todos.filter_by(completed=False)

    todos = todos.all()
    return render_template('search.html', todos=todos)


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)

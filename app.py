
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import case
from datetime import datetime, date

app = Flask(__name__) 
#Making Flask setting and defining database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Needs this for Flash, to show temporary msgs
app.secret_key = 'your_secret_key' 
db = SQLAlchemy(app)


#Inheriting class from db.Model of SQL alchemy, now SQL can use todomodel class to interact with database 
class TodoModel(db.Model):
    #Making Database schema, defining column entries
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    desc = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.Date, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(10), nullable=False, default='Medium')  


#To validate input means to remove extra spaces from input like starting extra spaces and ending extra spaces 
def validate_input(input_string):
    return input_string.strip()

#Defining the route of homepage, and this route able to handle two types of tasks get or post 
@app.route('/', methods=['GET', 'POST'])
def Home():

    #When user submits the form
    if request.method == 'POST':
        #Retreiving the value in the form that has the name of tile , desc...
        title = validate_input(request.form.get('title'))
        desc = validate_input(request.form.get('desc'))
        due_date = request.form.get('due_date')
        priority = request.form.get('priority')

        #if user didn;t enter title or desc then we show flash msg, to show error that is temporary
        if not title or not desc:
            flash("Both Title and Description are required.")
        else:
            #Otherwise setting the date, if user enters the date otherwise none, or validating the date
            due_date_obj = None

            if due_date:
                try:
                    #Converting string given by user into database data time format
                    due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                    if not (1900 <= due_date_obj.year <= 2100):
                        flash("Please enter a realistic year between 1900 and 2100.")
                        #refreshing the page
                        return redirect(url_for('Home'))
                    if due_date_obj < date.today():
                        flash("Due date cannot be earlier than today.")
                        return redirect(url_for('Home'))
                    #IT should be raised when the date entered by user is not in correct format, like incorrect day, month order

                except ValueError:
                    flash("Invalid date format. Please enter a valid date in YYYY-MM-DD format.")
                    return redirect(url_for('Home'))
            
            #Making instance of todo, by deifining schema of database
            todo = TodoModel(title=title, desc=desc, due_date=due_date_obj, priority=priority)
            #Adding task to the dataabase
            db.session.add(todo)
            #Saving task to the database
            db.session.commit()
            return redirect(url_for('Home'))
        
    #Making priority order, assigning numerical value to each task by priority
    priority_order = case(
        (TodoModel.priority == 'High', 1),
        (TodoModel.priority == 'Medium', 2),
        (TodoModel.priority == 'Low', 3),
        else_=4
    )

    # Filtring tasks if completed and ordering by priority order and then by due date   
    completed_tasks = TodoModel.query.filter_by(completed=True).order_by(priority_order, TodoModel.due_date).all()
    uncompleted_tasks = TodoModel.query.filter_by(completed=False).order_by(priority_order, TodoModel.due_date).all()

    #Passing all these variables to index.html file, where i will use them in a page of html
    return render_template('index.html', completed_tasks=completed_tasks, uncompleted_tasks=uncompleted_tasks, current_date=date.today())


#Route to today page, where i will show the tasks of today that are incompleted
@app.route('/today')
def today_tasks():
    today = date.today()
    today_todos = TodoModel.query.filter(TodoModel.due_date == today, TodoModel.completed == False).all()
    #returning these variables to today.html
    return render_template('today.html', today_todos=today_todos)


#Refreshing page of home, if user marks the incomplete todo to complete todo
@app.route('/toggle_complete/<int:id>', methods=['POST'])
def toggle_complete(id):
    #searching for the task in the database witch that sepcific id, it will give error 404 if that id or task not found.
    todo = TodoModel.query.get_or_404(id)
    #By searching that task, toggling its completion
    todo.completed = not todo.completed
    #Saving that to database and then refreshing the page
    db.session.commit()
    return redirect(url_for('Home'))


#For upadting specific task, making endpoint for that task
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    todo = TodoModel.query.get_or_404(id)

    if request.method == 'POST':
        title = validate_input(request.form.get('title'))
        desc = validate_input(request.form.get('desc'))
        due_date = request.form.get('due_date')
        priority = request.form.get('priority')  

        if title and desc:
            todo.title = title
            todo.desc = desc
            todo.priority = priority  

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


#for task details page, searching for that task and rednering task_Detial page.
@app.route('/task/<int:id>')
def task_detail(id):
    todo = TodoModel.query.get_or_404(id)
    return render_template('task_detail.html', todo=todo)


#Endpoint for deleteing speciific task from database and then refreshing the page
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    todo = TodoModel.query.get(id)
    if todo:
        db.session.delete(todo)
        #Saving the database
        db.session.commit()
    return redirect(url_for('Home'))


#Searching for specific taks by its id in the database and then displaying it
@app.route('/search', methods=['GET'])
def search():
    #Getting the query parameters, and getting the value of search otherwise empty string, same for priority and status
    search_query = request.args.get('search', '').strip()
    priority = request.args.get('priority')
    status = request.args.get('status')

    todos = TodoModel.query #Enabling query thing on database 
    if search_query:
        #Searching for any title that contains the searched word, no matter what comes before or after it
        todos = todos.filter(TodoModel.title.like(f"%{search_query}%"))
    #Matching the priorities and other things for search
    if priority:
        todos = todos.filter_by(priority=priority)
    if status == 'completed':
        todos = todos.filter_by(completed=True)
    elif status == 'uncompleted':
        todos = todos.filter_by(completed=False)

    todos = todos.all()
    return render_template('search.html', todos=todos)

#Route to about page, that tells user baout applicaiton
@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)

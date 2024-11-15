from app import app, db

with app.app_context():
    #Creating the table or making the defined schema in databse if not have
    db.create_all() 
    print("Database created successfully!")

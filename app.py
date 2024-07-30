#Task 1 Setting up Flask with Flask-SQLAlchemy
#flask-alchemy-assignment-venv activated
#pip install for flask, flask-marshmallow, and flask-sqlalchemy
#set interpreter for venv

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields, ValidationError
from password import my_password

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://root:{my_password}@127.0.0.1/fitness_center_database_assignment"
db = SQLAlchemy(app)
ma = Marshmallow(app)

class MemberSchema(ma.Schema):
    name = fields.Str(required=True)
    id = fields.Int(dump_only=True)
    age = fields.Int(required=True)

    class Meta:
        fields = ("name", "id", "age")

class WorkoutSessionSchema(ma.Schema):
    session_id = fields.Int(dump_only=True)
    member_id= fields.Int(required=True)
    session_date = fields.Date(required=True)
    session_time = fields.Str(required=True)
    activity = fields.Str(required=True)

    class Meta:
        fields = ("session_id", "member_id", "session_date", "session_time", "activity")

member_schema = MemberSchema()
members_schema = MemberSchema(many=True)

workout_session_schema = WorkoutSessionSchema()
workout_sessions_schema = WorkoutSessionSchema(many=True)

#define and call classes for Member and WorkoutSessions tables

class Member(db.Model):
    __tablename__ = "Members"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    workouts = db.relationship('WorkoutSession', backref='member')

class WorkoutSession(db.Model):
    __tablename__ = "WorkoutSessions"
    session_id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('Members.id'))
    session_date = db.Column(db.Date, nullable=False)
    session_time = db.Column(db.String(50), nullable=False)
    activity = db.Column(db.String(255), nullable=False)

#Defined WorkoutSessions and Members table models using SQLAlchemy for one to many relationship

with app.app_context():
    db.create_all()
#Creates tables for our models

#Task 2 Implementing CRUD Operations for Members using ORM

@app.route('/')
def home():
    return "Gym Management Database"

@app.route('/members', methods=['GET'])
def get_members():
    members = Member.query.all()
    return members_schema.jsonify(members)

#Gets all member data from the database by loading it into MembersSchema class and serializing it for POSTMAN in JSON

@app.route('/members', methods=['POST'])
def add_member():
    try:
        member_data = member_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages),400
    
    new_member = Member(name=member_data['name'], age=member_data['age'])
    db.session.add(new_member)
    db.session.commit()
    return jsonify({"message": "new member added successfully"}), 201

# Adds new member to database, commits the change and then returns a serialized JSON arguement in POSTMAN

@app.route('/members/<int:id>', methods=["PUT"])
def update_member(id):
    member = Member.query.get_or_404(id)
    try:
        member_data = member_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    member.name = member_data['name']
    member.age = member_data['age']
    db.session.commit()
    return jsonify({"message": "Member details updated successfully"}), 200

#Loads in updated values for name and age after looking up (via URL) id. Commits the change and then returns JSON serialized confirmation in POSTMAN

@app.route('/members/<int:id>', methods=['DELETE'])
def delete_member(id):
    member = Member.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    return jsonify({"message": "Member removed successfully"}), 200

# Looks up member to delete by id found in URL and if it finds this member it deletes it and then commits the change. Then returns serialized confirmation in POSTMAN

#Task 3 Managing Workout Sessions With ORM

@app.route('/workoutsessions', methods=['POST'])
def schedule_workout():
    try:
        workout_data = workout_session_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_workout = WorkoutSession(member_id=workout_data['member_id'], session_date=workout_data['session_date'], session_time=workout_data['session_time'], activity=workout_data['activity'])
    db.session.add(new_workout)
    db.session.commit()
    return jsonify({"message": "workout successfully scheduled"}), 201

'''
Tries to load in data in JSON from POSTMAN formatted like the WorkoutSession Schema, then creates a new_workout that calls the WorkoutSession class
categorizing the data that was loaded in, then adds the new workout and commits the change to our database. Lastly returns a serialized JSON message in POSTMAN to confirm the addition.
'''

@app.route('/workoutsessions/<int:session_id>', methods=['PUT'])
def update_workout(session_id):
    workout_session = WorkoutSession.query.get_or_404(session_id)
    try:
        session_data =  workout_session_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    workout_session.member_id = session_data['member_id']
    workout_session.session_date = session_data['session_date']
    workout_session.session_time = session_data['session_time']
    workout_session.activity = session_data['activity']
    db.session.commit()
    return jsonify({'message': 'workout session details successfully updated'}), 200
'''
Uses a query to retrieve id from URL in WorkoutSession class, and then attempts to load data from POSTMAN in a similar way to our schedule_workout() function
Once all JSON data is retrieved from POSTMAN and deserialized we assert this data as the new values for their appropriate categories in the database and commit the change.
The confirmation is serialized and returned as JSON to be viewed in POSTMAN
'''

@app.route('/workoutsessions', methods=['GET'])
def get_workout_session():
    workout_sessions = WorkoutSession.query.all()
    return workout_sessions_schema.jsonify(workout_sessions)

'''
Querries the entire WorkoutSessions table to return a serialized JSON response that we can view with all of our tables' rows in POSTMAN
'''

@app.route('/members/workouts-by-name', methods=['GET'])
def query_workout_by_member_name():
    name = request.args.get('name')
    member_id = Member.query.filter(Member.name == name).with_entities(Member.id).first()
    workouts = WorkoutSession.query.filter(WorkoutSession.member_id == member_id[0]).all()
    

    if workouts:
        return workout_sessions_schema.jsonify(workouts)
    else:
        return jsonify({"message": "workouts not found"}), 404

'''
I use our ORM and SQL-Alchemy to first get the name from our key:value in params in POSTMAN with request.args.get('name)
I then filter our search through the Member model by that name in the name column and focus in on the id column by using the syntax .with_entities(Member.id)
I next use that in the variable workouts to query the WorkoutSession model filtering the member_id foreign key column with the first item in the member_id tuple we just retrieved, listing all rows that meet that criteria.
If this results in a match I return the workout_sessions_schema as a JSON object in POSTMAN with values from our workouts variable.
If nothing is found I return a 404 message saying no workouts were found.
'''

if __name__ == "__main__":
    app.run(debug=True)

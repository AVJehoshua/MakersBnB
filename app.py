import os
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, session, Response, send_from_directory
from flask_bootstrap import Bootstrap
from s3_functions import upload_file
from werkzeug.utils import secure_filename
from flask_login import LoginManager



from lib.database_connection import get_flask_database_connection
from lib.space_repository import SpaceRepository
from lib.space import Space
from lib.login_repository import LoginRepository
from lib.login import LoginUser
from lib.login_validator import LoginValidator
from lib.users_repository import *
from lib.users import *
import boto3

import json
import secrets

# load env variables from .env file
load_dotenv()

# Create a new Flask app
app = Flask(__name__)
# UPLOAD_FOLDER = "uploads"
# BUCKET = "makersbnb"
Bootstrap(app)

login_manager = LoginManager()


"""
Route for landing page
"""
@app.route('/', methods=['GET'])
def landing():
    return render_template('users/index.html', access='denied')

"""
Route for signup page
"""

@app.route('/signUp', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        connection = get_flask_database_connection(app)
        repository = UserRepository(connection)
        user_name = request.form.get('user_name')
        email = request.form.get('email')
        user_password = request.form.get('user_password')
        print(f'Username: {user_name}, Email: {email}, Password: {user_password}')
        user = User(None, user_name, email, user_password)
        repository.create(user)
        return redirect('/login')
    return render_template('users/signUp.html', access='denied')

"""
Route for about page
"""

@app.route('/about', methods=['GET'])
def about():
    return render_template('users/about.html', access='granted', visibility='hidden')

"""
Routes for Users
"""


@app.route('/login',methods=['GET'])
def get_login():
    if 'token' in session:
      return redirect(f"/spaces")
    return render_template('login/login.html', access='denied')


@app.route("/login", methods=["POST"])
def login_user():
    if 'token' in session:
        return redirect(f"/spaces")
    connection = get_flask_database_connection(app)
    repository = LoginRepository(connection)
    validator = LoginValidator(
        request.form['user_name'],
        request.form['user_password']
    )
    if not validator.is_valid():
        errors = validator.generate_errors()
        return render_template("login/login.html", errors=errors)
        
    user_name = request.form['user_name']
    user_password = request.form['user_password']
    result = repository.find(user_name, user_password)

    print("result",result, "repository", repository)

    if result:
        token = secrets.token_urlsafe(64)
        session['token'] = token
        login = LoginUser(
            None,
            validator.get_valid_user_name(),
            validator.get_valid_user_password(),
            result.id
        )
        return redirect(f"/spaces")
    else:
        return Response(response={"error logging in"}, status=400, mimetype='application/json')
        


@app.route('/logout',methods=['GET'])
def get_logout():
    session.pop('token', None)
    print("session ended")
    return redirect(f"/")


"""
Routes for spaces
"""

@app.route('/spaces', methods=['GET'])
def get_spaces():
    if 'token' not in session:
      return render_template('users/index.html', access='denied')
    connection = get_flask_database_connection(app)
    repository = SpaceRepository(connection)
    spaces = repository.all()
    return render_template('spaces/spaces.html', spaces=spaces, visibility="hidden", access='granted')

@app.route('/list_a_space', methods=['GET'])
def get_list_a_space():
    return render_template('spaces/list_a_space.html', visibility="hidden", access='granted')

@app.route('/list_a_space', methods=['POST'])
def create_spaces():
    connection = get_flask_database_connection(app)
    repository = SpaceRepository(connection)
    # space = Space(None, request.form["space_name"], request.form["space_description"], "", request.form["price"], 1)
    print(request.files)

    img = request.files['space_image']
    if img:
        filename = secure_filename(img.filename)
        upload_path = os.path.join(app.root_path, 'static/image/')
        
        # Ensure the directory exists
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        
        img.save(os.path.join(upload_path, filename))
        msg = "Uploaded successfully!"
        print(msg)
        
    space = Space(None, request.form["space_name"], request.form["space_description"], filename, request.form["price"], 1)
    repository.create(space)
    return redirect('/spaces')



# @app.route("/upload", methods=['POST'])
# def upload():
#     if request.method == "POST":
#         f = request.files['file']
#         f.save(os.path.join(UPLOAD_FOLDER, secure_filename(f.filename)))
#         upload_file(f"uploads/{f.filename}", BUCKET)
#         return redirect("/spaces/list_a_space.html")



@app.route('/requests', methods=['GET'])
def get_requests_page():
    return render_template('spaces/requests.html', visibility="hidden", access='granted')

@app.route('/requests', methods=['POST'])
def submit_request():
    approved=False
    connection = get_flask_database_connection(app)
    repository = SpaceRepository(connection)
    user = request.form["user_name"]
    spaces = repository.find_by_username(user)

    return render_template('spaces/requests.html', spaces=spaces, approved=True, visibility="hidden", access='granted')



@app.route('/dist/<path:filename>')
def serve_static(filename):
    root_dir = os.path.dirname(os.getcwd())
    return send_from_directory(os.path.join(root_dir, 'dist'), filename)

# start the server and set the secret key and session type
if __name__ == '__main__':
    app.secret_key = b'secretkey'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True, port=int(os.environ.get('PORT', 4845)))
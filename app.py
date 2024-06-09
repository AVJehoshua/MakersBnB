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


"""
testing commit for pu
"""

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
Routes for file upload
"""


# app.route('/list_a_space', methods= "POST")
# def upload(): 
#         print(request.files)
#         img = request.files['space_photo']
#         if img:
#             filename = secure_filename(img.filename)
#             img.save(os.path.join(app.root_path, 'static/new_image', ))
#             msg = "Uploaded successfully!"
#         return render_template("/spaces/list_a_space.html", msg=msg)

# app.route("/upload", methods = ["POST"])

# def upload_file():
#     if "user_file" not in request.files:
#         return "No user_file key in request.files"

#     file = request.files["user_file"]

#     if file.filename == "":
#         return "Please select a file"

#     if file:
#         file.filename = secure_filename(file.filename)
#         output = send_to_s3(file, app.config["S3_BUCKET"])
#         return str(output)

#     else:
#         return redirect("/upload")



"""
Route for landing page
"""
@app.route('/', methods=['GET'])
def landing():
    return render_template('users/index.html', access='denied')

"""
Route for signup page
"""

@app.route('/signUp', methods=['GET'])
def sign_up():
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
    space = Space(None, request.form["space_name"], request.form["space_description"], request.form["price"], 1)
    # print("space photo data:", request.form["space_photo"])
    # BUCKET = "makersbnb"
    # upload = upload_file(request.form["space_photo"], BUCKET)
    repository.create(space) 
    print(request.files)
    img = request.files['space_photo']
    if img:
      filename = secure_filename(img.filename)
      img.save(os.path.join(app.root_path, 'static/image'))
      msg = "Uploaded successfully!"
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
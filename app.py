from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Database connection details
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Flask authentication setup.
app.secret_key = os.getenv('SECRET_KEY')
bcrypt = Bcrypt(app)


DATABASE_URL = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
engine = create_engine(DATABASE_URL)


# Flask login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Create a scoped session
Session = scoped_session(sessionmaker(bind=engine))
db_session = Session()

# Flask Login setup
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get(user_id):
        query = text("SELECT id, username, password FROM users WHERE id = :id")
        result = db_session.execute(query, {"id": user_id}).fetchone()
        if result:
            return User(*result)
        return None
    
    @staticmethod
    def find_by_username(username):
        query = text("SELECT id, username, password FROM users WHERE username = :username")
        result = db_session.execute(query, {"username": username}).fetchone()
        if result:
            return User(*result)
        return None
    
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        query = text("INSERT INTO users (username, password) VALUES (:username, :password)")
        try:
            db_session.execute(query, {"username": username, "password": hashed_password})
            db_session.commit()
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash("Error: " + str(e), "danger")
    
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.find_by_username(username)

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password", "danger")
    
    return render_template("login.html")




@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))


@app.route('/info', methods=['GET'])
@login_required
def index():
    return render_template("index.html", user=current_user)


@app.route('/last-row', methods=['GET'])
@login_required
def get_last_row():
    try:
        query = text("""
            SELECT * 
            FROM vervotech_update_data_info 
            ORDER BY created_at DESC 
            LIMIT 1;
        """)

        with engine.connect() as connection:
            result = connection.execute(query)
            row = result.fetchone()

            if row is None:
                return render_template("data_display.html", data=None)

            columns = result.keys()
            row_dict = dict(zip(columns, row))
            return render_template("data_display.html", data=row_dict)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/global-json-info', methods=['GET'])
@login_required
def get_json_data():
    try:
        query = text("""
            SELECT * 
            FROM vervotech_update_data_info 
            ORDER BY created_at DESC 
            LIMIT 1;
        """)

        with engine.connect() as connection:
            result = connection.execute(query)
            row = result.fetchone()

            if row is None:
                return jsonify({"error": "No data found"}), 404

            columns = result.keys()
            row_dict = dict(zip(columns, row))

            response = {
                "created_at": row_dict.get('created_at'),
                "total_vervotech_id": row_dict.get('total_vervotech_id'),
                "total_giata_id": row_dict.get('total_giata_id'),
                "update_info": {
                    "total_get_new": row_dict.get('vh_new_newFile'),
                    "find_new_data_success": row_dict.get('vh_new_newFile_updateSuccess'),
                    "find_new_data_skipping": row_dict.get('vh_new_newFile_updateSkipping'),
                    "new_file_last_update": row_dict.get('vh_new_newFile_lastUpdate_dateTime'),
                    "total_get_update": row_dict.get('vh_update_newFile'),
                    "find_update_data_success": row_dict.get('vh_update_newFile_updateSuccess'),
                    "find_update_data_skipping": row_dict.get('vh_update_newFile_updateSkipping'),
                    "update_file_last_update": row_dict.get('vh_update_newFile_lastUpdate_dateTime'),
                },
                "global_table": {
                    "total_global_table_id": row_dict.get('global_mapping_total'),
                    "global_table_new_add": row_dict.get('global_mapping_newFile'),
                    "new_data_add_time": row_dict.get('created_at'),
                    "new_content_update": row_dict.get('contentUpdatingStatus'),
                },
                "supplier_hotel_update_info": {
                    "hotelbeds": row_dict.get('hotelbeds'),
                    "ean": row_dict.get('ean'),
                    "agoda": row_dict.get('agoda'),
                    "mgholiday": row_dict.get('mgholiday'),
                    "restel": row_dict.get('restel'),
                    "stuba": row_dict.get('stuba'),
                    "hyperguestdirect": row_dict.get('hyperguestdirect'),
                    "tboglobal": row_dict.get('tbohotel'),
                    "goglobal": row_dict.get('goglobal'),
                    "ratehawkhotel": row_dict.get('ratehawkhotel'),
                    "adivahahotel": row_dict.get('adivahahotel'),
                    "grnconnect": row_dict.get('grnconnect'),
                    "juniper": row_dict.get('juniper'),
                    "mikihotel": row_dict.get('mikihotel'),
                    "paximumhotel": row_dict.get('paximumhotel'),
                    "adonishotel": row_dict.get('adonishotel'),
                    "w2mhotel": row_dict.get('w2mhotel'),
                    "oryxhotel": row_dict.get('oryxhotel'),
                    "dotw": row_dict.get('dotw'),
                    "hotelston": row_dict.get('hotelston'),
                    "lelsfly": row_dict.get('letsfly'),
                    "illusionshotel": row_dict.get('illusionshotel'),
                },
                "get_last_update_data": row_dict.get('lastUpdate')
            }

            return jsonify(response)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=2424)

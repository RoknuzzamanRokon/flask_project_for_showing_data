from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flask_talisman import Talisman
from flask_cors import CORS

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity


app = Flask(__name__)


# CORS: API is accessed from different domains
CORS(app)
# For security handle
load_dotenv()

# Database connection details
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Flask authentication setup.
app.secret_key = os.getenv('SECRET_KEY')
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # Replace with a strong secret key
jwt = JWTManager(app)



DATABASE_URL = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
engine = create_engine(DATABASE_URL)


# Create a scoped session
Session = scoped_session(sessionmaker(bind=engine))
db_session = Session()



# Flask login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# bcrypt = Bcrypt()
# db_session = scoped_session(sessionmaker())  # This is unbound!


# Initialize JWT
jwt = JWTManager(app)

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["60 per minute"]
)



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

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)





@app.route('/protected', methods=['GET'])
@jwt_required
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200



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



@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        username = request.json.get('username', None)
        password = request.json.get('password', None)
    else:
        username = request.form.get('username', None)
        password = request.form.get('password', None)

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    user = User.find_by_username(username)
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401



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
@jwt_required
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
                    "tbohotel": row_dict.get('tbohotel'),
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
                "supplier_hotel_total_data_count": {
                    "hotelbeds": row_dict.get('hotelbeds_total_hotel_ids'),
                    "ean": row_dict.get('ean_total_hotel_ids'),
                    "agoda": row_dict.get('agoda_total_hotel_ids'),
                    "mgholiday": row_dict.get('mgholiday_total_hotel_ids'),
                    "restel": row_dict.get('restel_total_hotel_ids'),
                    "stuba": row_dict.get('stuba_total_hotel_ids'),
                    "hyperguestdirect": row_dict.get('hyperguestdirect_total_hotel_ids'),
                    "tbohotel": row_dict.get('tbohotel_total_hotel_ids'),
                    "goglobal": row_dict.get('goglobal_total_hotel_ids'),
                    "ratehawkhotel": row_dict.get('ratehawkhotel_total_hotel_ids'),
                    "adivahahotel": row_dict.get('adivahahotel_total_hotel_ids'),
                    "grnconnect": row_dict.get('grnconnect_total_hotel_ids'),
                    "juniper": row_dict.get('juniper_total_hotel_ids'),
                    "mikihotel": row_dict.get('mikihotel_total_hotel_ids'),
                    "paximumhotel": row_dict.get('paximumhotel_total_hotel_ids'),
                    "adonishotel": row_dict.get('adonishotel_total_hotel_ids'),
                    "w2mhotel": row_dict.get('w2mhotel_total_hotel_ids'),
                    "oryxhotel": row_dict.get('oryxhotel_total_hotel_ids'),
                    "dotw": row_dict.get('dotw_total_hotel_ids'),
                    "hotelston": row_dict.get('hotelston_total_hotel_ids'),
                    "lelsfly": row_dict.get('letsfly_total_hotel_ids'),
                    "illusionshotel": row_dict.get('illusionshotel_total_hotel_ids'),
                    
                },
                "get_last_update_data": row_dict.get('lastUpdate'),
                "vervotech_ids_total": row_dict.get('vervotech_ids_total'),
                "giata_ids_total": row_dict.get('giata_ids_total'),
            }

            return jsonify(response)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500



from datetime import datetime

@app.route('/dashboard', methods=['GET'])
@jwt_required
def dashboard():
    try:
        # Get all historical data
        query = text("""
            SELECT *, DATE(created_at) as date 
            FROM vervotech_update_data_info 
            ORDER BY created_at DESC;
        """)

        with engine.connect() as connection:
            result = connection.execute(query)
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in result.fetchall()]
        
        # Ensure date is properly formatted
        for entry in data:
            if isinstance(entry['date'], str): 
                entry['date'] = datetime.strptime(entry['date'], '%Y-%m-%d')

        # Prepare chart data
        chart_data = {
            'dates': [entry['date'].strftime('%Y-%m-%d') for entry in data],
            'total_mappings': [int(entry.get('global_mapping_total', 0)) for entry in data],
            'new_success': [int(entry.get('vh_new_newFile_updateSuccess', 0)) for entry in data],
            'update_success': [int(entry.get('vh_update_newFile_updateSuccess', 0)) for entry in data],
            'success_ratio': [
                (int(entry.get('vh_new_newFile_updateSuccess', 0)) + 
                 int(entry.get('vh_update_newFile_updateSuccess', 0))) / 
                max((int(entry.get('vh_new_newFile', 0)) + 
                     int(entry.get('vh_update_newFile', 0))), 1) * 100  # Avoid division by zero
                for entry in data
            ]
        }

        # Add project milestones data
        chart_data['project_milestones'] = {
            'phases': ['Phase 1: Data Collection', 'Phase 2: System Integration', 
                       'Phase 3: Testing', 'Phase 4: Deployment'],
            'progress': [100, 100, 75, 30]  # Example percentages
        }

        return render_template(
            "dashboard.html",
            data=data,
            chart_data=chart_data,
            latest=data[0] if data else None
        )

    except Exception as e:
        print(f"Dashboard Error: {e}")
        flash(f"Error loading data: {str(e)}", "danger")
        return redirect(url_for('index')) 
    

if __name__ == '__main__':
    app.run(debug=True, port=2424)

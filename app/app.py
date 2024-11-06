from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response
import requests
import logging
from databases import fetch_data_from_table, admin_verify, update_conversation_title, get_session_from_conversation, session_continue, connect_db, user_exists, end_session, session, session_exists, conversation, insert_user, get_transcripts, add_conversation, get_conversation_id, write_feedback, upload_pending_FAQ, session_valid, error_logs, get_all_conversations
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import re
from flask_cors import CORS
from dotenv import load_dotenv
import os
from ldap3 import Server, Connection, ALL, SUBTREE
import uuid
import jwt  # For token handling
from zoneinfo import ZoneInfo
import pandas as pd
from decorators import admin_required
from flask import send_from_directory, abort
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Cho phép tất cả nguồn gốc

UPLOAD_FOLDER = '/app/save_files'  # Đường dẫn trong container
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Giới hạn kích thước file upload lên tới 16MB
ALLOWED_EXTENSIONS = {'docx', 'md', 'pdf'}  # Định nghĩa các định dạng file cho phép


# Set up logging
logging.basicConfig(level=logging.DEBUG)

load_dotenv()

CHATBOT_APIKEY = os.getenv('CHATBOT_APIKEY')
CHATBOT_URL = os.getenv('CHATBOT_URL')
LDAP_SERVER = os.getenv('LDAP_SERVER')
LDAP_USER = os.getenv('LDAP_USER')
LDAP_PASSWORD = os.getenv('LDAP_PASSWORD')
BASE_DN = os.getenv('BASE_DN')
SECRET_KEY = os.getenv('SECRET_KEY')
SECRET_TOKEN = os.environ.get('SECRET_TOKEN')  # Lấy token từ biến môi trường

# Kiểm tra định dạng file được phép upload
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Tạo tên file mới bao gồm 'NămThángNgày_GiờPhútGiây' và tên gốc của file
def generate_new_filename(original_filename):
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    original_name = secure_filename(original_filename.rsplit('.', 1)[0])
    extension = original_filename.rsplit('.', 1)[1].lower()
    new_filename = f"{current_time}_{original_name}.{extension}"
    return new_filename

# Xác thực token
def verify_secret_token():
    token = request.headers.get('Authorization')
    if token != SECRET_TOKEN:
        abort(401)  # Unauthorized

# Route để upload file
@app.route('/upload', methods=['POST'])
def upload_file():
    verify_secret_token()  # Kiểm tra token trước khi xử lý
    if 'file' not in request.files:
        return {'error': 'No file part in request'}, 400
    file = request.files['file']
    if file.filename == '':
        return {'error': 'No selected file'}, 400
    if file and allowed_file(file.filename):
        new_filename = generate_new_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        file.save(filepath)
        download_url = url_for('download_file', filename=new_filename, _external=True)
        return {'message': 'File uploaded successfully', 'download_url': download_url}
    else:
        return {'error': 'Unsupported file format'}, 415

# Route để download file (không yêu cầu token)
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    # Không yêu cầu xác thực token ở đây
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def decode_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = decoded.get('user_id')
        exp = decoded.get('exp')
        if user_id and exp:
            # Verify token has not expired
            if datetime.utcnow().timestamp() < exp:
                return user_id
            else:
                # Token has expired
                return None
        else:
            # Invalid token payload
            return None
    except jwt.ExpiredSignatureError:
        # Token has expired
        return None
    except jwt.InvalidTokenError:
        # Invalid token
        return None

@app.route('/api/verify_token', methods=['POST'])
def api_verify_token():
    data = request.json
    token = data.get('token')
    logging.debug(f"Token verification request: {token}")
    
    user_id = decode_token(token)
    
    if user_id:
        conn = connect_db()
        session_id = session_continue(conn, user_id)
        if not session_id:
            session_id = f"{uuid.uuid4()}"
        if isinstance(session_id, tuple):
            session_id = session_id[0]
        
        return jsonify({
            'user_id': user_id,
            'session_id': session_id
        })
    else:
        logging.warning(f"Token verification failed")
        return jsonify({'error': 'Invalid token'}), 401


@app.after_request
def add_security_headers(response):
    # Bỏ 'X-Frame-Options' để không hạn chế việc nhúng iframe
    response.headers.pop('X-Frame-Options', None)

    # Cho phép tất cả các domain nhúng iframe
    response.headers['Content-Security-Policy'] = "frame-ancestors *"
    return response

def authenticate_user(username, password):
    try:
        # Nếu username chứa domain (vd: pv-power\ldap_admin), tách ra
        if '\\' in username:
            username, domain = username.split('\\', 1)
        
        if '@' in username:
            username, domain = username.split('@', 1)

        logging.debug(f"Authenticating user: {username}")

        server = Server(LDAP_SERVER, get_info=ALL)
        conn = Connection(server, user=LDAP_USER, password=LDAP_PASSWORD, auto_bind=True)
        
        # Tìm kiếm DN của người dùng trong tất cả các OUs
        search_filter = f"(sAMAccountName={username})"
        conn.search(search_base=BASE_DN, search_filter=search_filter, search_scope=SUBTREE, attributes=['distinguishedName'])
        
        if not conn.entries:
            logging.debug("User DN not found.")
            return False, 'Người dùng không tồn tại.'

        user_dn = conn.entries[0].distinguishedName.value
        
        # Thử xác thực người dùng với DN và mật khẩu
        user_conn = Connection(server, user=user_dn, password=password, auto_bind=True)
        logging.debug(f"User {username} authenticated successfully.")
        return True, 'Đăng nhập thành công!'
    except Exception as e:
        logging.error(f"Lỗi LDAP: {str(e)}")
        return False, f'Lỗi LDAP: {str(e)}'

@app.route('/')
def home():
    session_id = request.cookies.get('session_id')
    user_id = request.cookies.get('user_id')

    if not session_id:
        logging.debug("No session_id found, redirecting to signin.")
        return redirect(url_for('signin'))

    # Kiểm tra xem người dùng có phải là admin không
    conn = connect_db()
    is_admin = admin_verify(conn, user_id)  # Giả định rằng bạn đã truyền kết nối `conn`

    logging.debug(f"Rendering home page for user_id: {user_id}, session_id: {session_id}, is_admin: {is_admin}")
    return render_template('index.html', is_admin=is_admin)

@app.route('/chatbot')
def chatbot():
    # Lấy session_id và user_id từ cookie
    session_id = request.cookies.get('session_id')
    user_id = request.cookies.get('user_id')

    # Nếu không có session_id và user_id trong cookie, kiểm tra query parameter
    token = request.args.get('token')
    if not session_id or not user_id:
        if token:
            # Nếu có token trong URL, xác thực token
            logging.debug(f"Token found in URL: {token}")
            user_id = decode_token(token)
    
            if user_id:
                conn = connect_db()
                session_id = session_continue(conn, user_id)
                if not session_id:
                    session_id = f"{uuid.uuid4()}"
                if isinstance(session_id, tuple):
                    session_id = session_id[0]
                
                logging.debug(f"Token valid. Decoded user_id: {user_id}")
                
                # Set cookies cho session_id và user_id
                expires = datetime.now(timezone.utc) + timedelta(minutes=60)
                response = make_response(redirect(url_for('chatbot', token=token)))  # Chuyển hướng về /chatbot và giữ lại token
                response.set_cookie('session_id', session_id, expires=expires, samesite='None', secure=True)
                response.set_cookie('user_id', user_id, expires=expires, samesite='None', secure=True)
                return response
            else:
                logging.debug("Invalid token. Redirecting to signin.")
                return redirect(url_for('signin', token=token))  # Redirect tới signin và giữ lại token
        else:
            # Nếu không có token trong query parameter, redirect về signin
            logging.debug("No session_id or token found. Redirecting to signin.")
            return redirect(url_for('signin'))

    # Nếu có session_id và user_id hợp lệ
    logging.debug(f"Rendering chatbot for user_id: {user_id}, session_id: {session_id}")
    return render_template('chatbot.html')


@app.route('/chatbot_index')
def chatbot_index():
    session_id = request.cookies.get('session_id')
    user_id = request.cookies.get('user_id')

    if not session_id:
        logging.debug("No session_id found, redirecting to signin.")
        # return redirect(url_for('signin'))

    logging.debug(f"Rendering home page for user_id: {user_id}, session_id: {session_id}")
    return render_template('chatbot_index.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')


        logging.debug(f"Received POST request for signin with username: {username}")

        if not username or not password:
            logging.warning("Username or password missing.")
            return render_template('signin.html', error="Username or password is missing.")
        
        if CHATBOT_URL != "http://192.168.17.50:9081/v1":
            success = True
            message = "Thành Công!"
            conn_db = connect_db()
            if not user_exists(conn_db, username):
                insert_user(conn_db, username, username)
        else:
            success, message = authenticate_user(username, password)
            conn_db = connect_db()
            if not user_exists(conn_db, username):
                insert_user(conn_db, username, username)
            if conn_db:
                logging.debug("Connected to the database successfully.")
            else:
                logging.error("Failed to connect to the database.")
            logging.debug(f"Creating new user if not exist: {username}")
            try:
                logging.debug(f"Attempting to insert user: {username}")
                insert_user(conn_db, username, username)
                logging.debug(f"User {username} inserted successfully.")
            except Exception as e:
                logging.error(f"Error occurred in insert_user: {str(e)}")

        
        if success:
            conn = connect_db()
            session_id = session_continue(conn, username)
            if not session_id:
                session_id = f"{uuid.uuid4()}"
            if isinstance(session_id, tuple):
                session_id = session_id[0]
            logging.debug(f"Redirecting to home with session_id: {session_id}")
            
            # Set cookie for session_id and user_id
            response = make_response(redirect(url_for('home')))
            # Đặt thời gian hết hạn cụ thể, ví dụ 10 phút kể từ bây giờ
            expires = datetime.now(timezone.utc) + timedelta(minutes=60)
            
            # Đặt cookie với thời gian hết hạn cụ thể
            response.set_cookie('session_id', session_id, expires=expires)
            response.set_cookie('user_id', username, expires=expires)

            return response
        else:
            logging.warning(f"Authentication failed: {message}")
            return render_template('signin.html', error=message)
    
    logging.debug("Rendering signin page.")
    return render_template('signin.html')



@app.route('/api/message', methods=['GET'])
def api_message():
    conn = connect_db()
    user_id = request.args.get('user_id')
    user_message = request.args.get('text')
    session_id = request.args.get('session_id')
    conversation_id = request.args.get('conversation_id')

    end_session(conn, user_id, session_id)

    if not user_message:
        error_logs(user_id, session_id, conversation_id, user_message, "No message provided", "400")
        return jsonify({"result": "No message provided"}), 400
    
    transcripts = get_transcripts(conn, user_id, session_id)
    transcripts = json.dumps(transcripts)
    print(conversation_id, transcripts, user_message, user_id, session_id)

    url = f'{CHATBOT_URL}/chat-messages'
    headers = {
        'Authorization': f'Bearer {CHATBOT_APIKEY}',
        'Content-Type': 'application/json'
    }

    body = {
        "inputs": {},
        "query": user_message,
        "response_mode": "blocking",
        "conversation_id": conversation_id if conversation_id else "",
        "user": user_id
    }
    print(body)
    try:
        
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()

        result = response.json()

        print("Result:", result)
        result_answer = decode_unicode_escapes(result["answer"])
        domain = extract_domain(result_answer)
        input_token = len(user_message)//4 + 1
        output_token = len(result)//4 + 1
        total_token = input_token + output_token
        timestamp = datetime.now(ZoneInfo('Asia/Ho_Chi_Minh'))
        timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S %z')
        print(result["message_id"])
        conversation(conn, result["message_id"], session_id, user_id, "gpt", user_message, input_token, result_answer[:-len(domain)-1], output_token, total_token, timestamp, conversation_id, domain)
        conn.close()
        print("Done!")
        return jsonify({"result": result_answer, "message_id": result["message_id"]})

    except requests.exceptions.RequestException as e:
        app.logger.error(f"RequestException: {e}")
        error_code = e.response.status_code
        error_logs(conn, user_id, session_id,  conversation_id or '', user_message, 'Send message failed due to ' + str(e), error_code)
        return jsonify({"result": f"Xin lỗi, tôi không đủ thông tin để trả lời câu hỏi này"}), error_code
    except Exception as e:
        app.logger.error(f"Exception: {e}")
        error_code = e.response.status_code
        error_logs(conn, user_id, session_id, conversation_id or '', user_message, 'Send message failed due to ' + str(e), error_code)
        return jsonify({"result": f"Xin lỗi, tôi không đủ thông tin để trả lời câu hỏi này"}), error_code


@app.route('/api/start_conversation', methods=['POST'])
def start_conversation():
    conn = connect_db()
    user_id = request.json['user_id']
    session_id = request.json['session_id']

    url = f'{CHATBOT_URL}/chat-messages'
    headers = {
        'Authorization': f'Bearer {CHATBOT_APIKEY}',
        'Content-Type': 'application/json'
    }
    body = {
        "inputs": {},
        "query": "Xin chào",
        "response_mode": "blocking",
        "conversation_id": "",
        "user": user_id
    }
    app.logger.info(f"Headers: {headers}")
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()

        data = response.json()
        conversation_id = data['conversation_id']

        result = response.json()

        print("Result:", result)
        result_answer = decode_unicode_escapes(result["answer"])
        domain = extract_domain(result_answer)
        input_token = 0
        output_token = len(result)//4 + 1
        total_token = input_token + output_token
        timestamp = datetime.now(ZoneInfo('Asia/Ho_Chi_Minh'))
        timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S %z')

        add_conversation(conn, conversation_id, "New message", session_id, user_id)
        conversation(conn, data["message_id"], session_id, user_id, "gpt", "", input_token, result_answer[:-len(domain)-1], output_token, total_token, timestamp, conversation_id, domain)
        logging.debug(f"Conversation {conversation_id} inserted successfully.")
        conn.close()
        return jsonify({"conversation_id": conversation_id, "message_id": result["message_id"]})
    except requests.exceptions.RequestException as e:
        app.logger.error(f"RequestException: {e}")
        error_code = e.response.status_code
        error_logs(conn, user_id, session_id, '', '', 'Start conversation failed due to ' + str(e), error_code)
        return jsonify({"result": f"Xin lỗi, tôi không đủ thông tin để trả lời câu hỏi này"}), error_code
    except Exception as e:
        app.logger.error(f"Exception: {e}")
        error_code = e.response.status_code
        error_logs(conn, user_id, session_id, '', '', 'Start conversation failed due to ' + str(e), error_code)
        return jsonify({"result": f"Xin lỗi, tôi không đủ thông tin để trả lời câu hỏi này"}), error_code

@app.route('/api/user', methods=['POST'])
def api_user():
    conn = connect_db()
    user_id = request.json['user_id']
    if not user_exists(conn, user_id):
        insert_user(conn, user_id, user_id)
    conn.close()
    return jsonify({"result": "User added successfully"})

@app.route('/api/user_exist', methods=['POST'])
def user_exist():
    conn = connect_db()
    user_id = request.json['user_id']
    exists = user_exists(conn, user_id)
    if not exists:
        return jsonify({"result": 0}), 404
    conn.close()
    return jsonify({"result": 1})

@app.route('/api/chat_status', methods=['GET'])
def api_chat_status():
    conn = connect_db()
    data = request.get_json()
    token = data.get('token')
    user_id = decode_token(token)
    app.logger.debug(f"user_id: {user_id}")
    
    if not user_exists(conn, user_id):
        return jsonify({"result": "User does not exist"}), 404
    if not session_valid(conn, user_id):
        return jsonify({"result": 0})
    return jsonify({"result": 1})
    
@app.route('/api/session', methods=['POST'])
def api_session():
    conn = connect_db()
    user_id = request.json['user_id']
    session_id = request.json['session_id']
    start_time = request.json['start_time']
    end_time = request.json['end_time']
    
    session(conn, user_id, session_id, start_time, end_time)
    conn.close()
    return jsonify({"result": "Session added successfully"})

@app.route('/api/session_exist', methods=['POST'])
def api_session_exist():
    conn = connect_db()
    user_id = request.json['user_id']
    session_id = request.json['session_id']
    if not session_exists(conn, user_id, session_id):
        return jsonify({"result": 0}), 404
    if not session_valid(conn, user_id):
        return jsonify({"result": "session expired"}), 404
    conn.close()
    return jsonify({"result": 1})

@app.route('/api/conversation_id', methods=['POST'])
def api_conversation_id():
    conn = connect_db()
    user_id = request.json['user_id']
    session_id = request.json['session_id']

    conversation_id = get_conversation_id(conn, user_id, session_id)

    if conversation_id is None:
        return jsonify({"result": "Conversation ID not found"}), 404
    else:
        return jsonify({"result": conversation_id[0]})
    
@app.route('/api/feedback', methods=['POST'])
def api_feedback():
    conn = connect_db()
    data = request.json  # Thay đổi để lấy toàn bộ dữ liệu JSON
    user_id = data.get('user_id')
    session_id = data.get('session_id')
    message_id = data.get('messageId')  # Đảm bảo sử dụng đúng tên khóa
    feedback_type = data.get('feedbackType')
    feedback_text = data.get('feedbackText', '')
    
    write_feedback(conn, user_id, session_id, message_id, feedback_type, feedback_text)
    conn.close()
    return jsonify({"result": "Feedback added successfully"})

@app.route('/api/get_transcripts', methods=['POST'])
def api_transcripts():
    conn = connect_db()
    data = request.json
    user_id = data.get('user_id')
    session_id = data.get('session_id')
    transcripts = get_transcripts(conn, user_id, session_id)
    # Thêm logging để kiểm tra dữ liệu trả về
    app.logger.debug(f"Transcripts for user_id={user_id}, session_id={session_id}: {transcripts}")
    return jsonify({"transcripts": json.dumps(transcripts)})

def decode_unicode_escapes(string):
    # This function will only decode the Unicode escape sequences, not the emojis
    unicode_escape_pattern = re.compile(r'\\u[0-9a-fA-F]{4}')
    return unicode_escape_pattern.sub(lambda m: chr(int(m.group(0)[2:], 16)), string)

@app.route('/api/upload_pending_FAQ', methods=['POST'])
def upload_pending_faq():
    conn = connect_db()
    data = request.json
    question = data.get('question')
    answer = data.get('answer')
    domain = data.get('domain')
    user_id = data.get('user_id')
    upload_pending_FAQ(conn, question, answer, domain, user_id)
    conn.close()
    return jsonify({"result": "FAQ uploaded successfully"})

@app.route('/embed')
def embed():
    user_id = request.args.get('user_id')
    session_id = request.args.get('session_id')

    if not user_id or not session_id:
        return redirect(url_for('signin'))

    # Tạo đối tượng response trước
    response = make_response(render_template('chatbot.html'))

    # Đặt cookies mà không chỉ định domain
    response.set_cookie('session_id', session_id, max_age=1, path='/')
    response.set_cookie('user_id', user_id, max_age=1, path='/')

    return response

def extract_domain(input_string):
            match = re.search(r'False', input_string)
            if match:
                matchGroup = re.search(r'False Group \d+ Doc', input_string)
                if matchGroup:
                    return matchGroup.group(0)
                else:
                    return match.group(0)
            else:
                return "True"

@app.route('/get_all_conversations', methods=['POST'])
def all_conversations():
    data = request.json
    user_id = data.get('user_id')

    conn = connect_db()
    conversations = get_all_conversations(conn, user_id)
    conn.close()

    today = datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).date()
    yesterday = today - timedelta(days=1)
    seven_days_ago = today - timedelta(days=7)

    # Nhóm các cuộc hội thoại
    grouped_conversations = {
        "today": [],
        "yesterday": [],
        "last_7_days": []
    }


    app.logger.debug(f"conversations: {conversations}")
    for conversation in conversations:
        
        conversation_title = conversation[1] if conversation[1] else "New conversation"
        created_at = conversation[2].date()

        # Kiểm tra và chỉ đưa cuộc hội thoại vào 1 nhóm duy nhất
        if created_at == today:
            grouped_conversations["today"].append({
                'conversation_id': conversation[0],
                'conversation_title': conversation_title
            })
        elif created_at == yesterday:
            grouped_conversations["yesterday"].append({
                'conversation_id': conversation[0],
                'conversation_title': conversation_title
            })
        elif created_at >= seven_days_ago and created_at < yesterday:
            grouped_conversations["last_7_days"].append({
                'conversation_id': conversation[0],
                'conversation_title': conversation_title
            })

    return jsonify(grouped_conversations)

@app.route('/create_new_conversation', methods=['POST'])
def create_new_conversation():
    user_id = request.json.get('user_id')

    # Tạo session_id mới
    session_id = str(uuid.uuid4())

    # Lấy thời gian hiện tại theo UTC và cộng thêm 7 giờ
    now_utc = datetime.utcnow()
    now_gmt7 = now_utc + timedelta(hours=7)  # Chuyển sang GMT+7

    # Lưu thời gian bắt đầu và kết thúc
    start_time = now_gmt7.strftime("%Y-%m-%d %H:%M:%S %z")
    end_time = (now_gmt7 + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S %z")


    # Lưu session vào database (hoặc hệ thống lưu trữ của bạn)
    conn = connect_db()
    session(conn, user_id, session_id, start_time, end_time) 
    conn.close()

    # Đặt session_id vào cookie với thời gian hiệu lực 30 phút
    response = make_response(jsonify({'message': 'New session created', 'session_id': session_id}))
    response.set_cookie('session_id', session_id, max_age=1800)  # 1800 giây = 30 phút
    return response

@app.route('/api/get_session_id', methods=['POST'])
def get_session_id():
    conversation_id = request.json.get('conversation_id')
    
    conn = connect_db()
    session_id = get_session_from_conversation(conn, conversation_id)
    conn.close()

    if session_id:
        return jsonify({'session_id': session_id[0]})
    else:
        return jsonify({'error': 'Conversation ID not found'}), 404


@app.route('/api/update_conversation_title', methods=['POST'])
def update_conversation_title_api():
    conn = connect_db()
    data = request.json
    user_id = data.get('user_id')
    session_id = data.get('session_id')
    conversation_id = data.get('conversation_id')

    # Lấy transcripts
    transcripts = get_transcripts(conn, user_id, session_id)
    app.logger.debug(f"Original transcripts: {transcripts}")

    # Parse JSON nếu transcripts là chuỗi JSON
    if isinstance(transcripts, str):
        try:
            transcripts = json.loads(transcripts)
            app.logger.debug(f"Parsed JSON transcripts: {transcripts}")
        except json.JSONDecodeError as e:
            app.logger.error(f"Error parsing transcripts JSON: {e}")
            conn.close()
            return jsonify({'result': 'Error parsing transcripts'}), 500

    # Nếu transcripts là một danh sách chứa tuple, ta lấy phần tử đầu tiên (tuple)
    if isinstance(transcripts, list) and len(transcripts) > 0:
        transcripts_tuple = transcripts[0]
        # app.logger.debug(f"Extracted first tuple from transcripts: {transcripts_tuple}")

        # Transcripts_tuple là một tuple, lấy phần đầu tiên là danh sách các tin nhắn
        if isinstance(transcripts_tuple, tuple) and len(transcripts_tuple) > 0:
            messages = transcripts_tuple[0]
            # app.logger.debug(f"Extracted messages from transcripts_tuple: {messages}")

            # Lọc ra các tin nhắn của người dùng
            user_messages = [msg for msg in messages if msg.get('role') == 'user' and msg.get('text')]
            # app.logger.debug(f"Filtered user messages: {user_messages}")

            if len(user_messages) >= 1:
                second_user_message = user_messages[0]['text']
                app.logger.debug(f"Second user message: {second_user_message}")

                # Cập nhật tiêu đề cuộc hội thoại
                update_conversation_title(conn, conversation_id, second_user_message)
                conn.close()
                return jsonify({'result': 'Title updated', 'new_title': second_user_message})
            else:
                app.logger.debug(f"Not enough user messages to update title")
                conn.close()
                return jsonify({'result': 'Not enough user messages to update title'}), 400
        else:
            app.logger.error(f"Unexpected structure in transcripts_tuple: {transcripts_tuple}")
            conn.close()
            return jsonify({'result': 'Error in transcripts structure'}), 500
    else:
        app.logger.error(f"Unexpected structure in transcripts: {transcripts}")
        conn.close()
        return jsonify({'result': 'Error in transcripts structure'}), 500

@app.route('/admin', methods=['GET'])
@admin_required
def admin_dashboard():
    error_logs_df = fetch_data_from_table("error_logs")
    # Fetch dữ liệu từ database
    users_df = fetch_data_from_table('users')
    conversation_logs_df = fetch_data_from_table('conversation_logs')
    feedback_df = fetch_data_from_table('feedback')
    session_df = fetch_data_from_table('sessions')

    # Lấy danh sách user_id
    user_list = users_df['user_id'].unique().tolist()
    
    # Tổng hợp số liệu
    total_users = users_df['user_id'].nunique()
    total_messages = conversation_logs_df['message_id'].count()
    total_sessions = conversation_logs_df['session_id'].nunique()

    # Tính thời lượng chat trung bình
    conversation_logs_df['timestamp'] = pd.to_datetime(conversation_logs_df['timestamp'])
    conversation_logs_df['created_at'] = pd.to_datetime(conversation_logs_df['created_at'])

    # Calculate session start and end times based on the first and last message timestamps
    session_start_times = conversation_logs_df.groupby('session_id')['timestamp'].min().reset_index()
    session_start_times.columns = ['session_id', 'start_time']
    session_end_times = conversation_logs_df.groupby('session_id')['timestamp'].max().reset_index()
    session_end_times.columns = ['session_id', 'end_time']
    
    # Merge start and end times into a single DataFrame
    session_times = pd.merge(session_start_times, session_end_times, on='session_id')

    # Calculate session durations
    session_times['session_duration'] = (session_times['end_time'] - session_times['start_time']).dt.total_seconds()

    avg_session_duration = round(session_times['session_duration'].mean(), 2)

    # Tính tỷ lệ lỗi chatbot
    if total_sessions > 0:
        errored_sessions = conversation_logs_df[conversation_logs_df['outputs'].str.contains('error|fail|not found|unable', case=False)]
        error_rate = round((errored_sessions['session_id'].nunique() / total_sessions) * 100, 2)
    else:
        error_rate = 0.0  # Nếu không có session nào, tỷ lệ lỗi đặt bằng 0

    # Tính thời gian phản hồi trung bình
    conversation_logs_df['response_speed'] = (abs((conversation_logs_df['timestamp'] - conversation_logs_df['created_at']))).dt.total_seconds()
    avg_response_time = round(conversation_logs_df['response_speed'].mean(), 2)

    # Chuẩn bị dữ liệu cho biểu đồ
    user_messages_data = conversation_logs_df.groupby(conversation_logs_df['timestamp'].dt.date).size().to_dict()
    user_messages_data = {str(key): value for key, value in user_messages_data.items()}  # Chuyển datetime thành chuỗi

    hourly_messages_data = conversation_logs_df.groupby(conversation_logs_df['timestamp'].dt.hour).size().to_dict()

    # Tính tỷ lệ phản hồi người dùng
    feedback_subset = feedback_df[['message_id', 'feedback_type', 'feedback_text']]
    logging.info("Feedback Counts: %s", feedback_subset)
    conversation_logs_df_feedback = pd.merge(conversation_logs_df, feedback_subset, on='message_id', how='left')
    conversation_logs_df_feedback = conversation_logs_df_feedback.drop_duplicates(subset=['message_id'])
    # Tính toán số lượng mỗi loại feedback_type
    # Thay thế NaN bằng "No Feedback"
    conversation_logs_df_feedback['feedback_type'] = conversation_logs_df_feedback['feedback_type'].fillna('no_feedback')

    feedback_counts = conversation_logs_df_feedback['feedback_type'].value_counts().to_dict()

    # Xử lý dữ liệu người dùng theo ngày
    session_df['created_at'] = pd.to_datetime(session_df['created_at']).dt.date
    users_by_date = session_df.groupby('created_at').size().to_dict()
    users_by_date_str = {str(k): v for k, v in users_by_date.items()}  # Chuyển datetime thành chuỗi

    # Log để kiểm tra dữ liệu JSON
    logging.info("Feedback Counts: %s", feedback_counts)
    logging.info("User Messages Data: %s", user_messages_data)
    logging.info("Hourly Messages Data: %s", hourly_messages_data)
    logging.info("User Access Data: %s", users_by_date_str)

    non_faqs_df = conversation_logs_df[conversation_logs_df['inputs'] != ""]

    # Creating the Non_FAQs_df
    non_faqs_df = non_faqs_df[['message_id', 'inputs', 'outputs', 'domain']].copy()
    non_faqs_df['usage_count'] = non_faqs_df.groupby('inputs')['inputs'].transform('count')
    non_faqs_df = non_faqs_df[['message_id', 'inputs', 'domain', 'usage_count', 'outputs']]
    non_faqs_df.columns = ['question_id', 'text_content', 'domain', 'usage_count', 'outputs']
    non_faqs_df_used = non_faqs_df[['text_content', 'usage_count', 'outputs']]

    # Sort by 'usage_count' in descending order
    non_faqs_df_used = non_faqs_df_used.sort_values(by='usage_count', ascending=False)
    non_faqs_df_used = non_faqs_df_used.drop_duplicates(subset='text_content', keep='first')
    non_faqs_data = non_faqs_df_used.to_dict(orient='records')

    first_date = users_df['created_at'].min().date()

    # Sửa lại cách lấy ngày hôm nay
    today_date = datetime.now().date()
    logging.info("today_date: %s", today_date)

    return render_template(
        'admin_dashboard.html',
        first_date=first_date,  # Truyền ngày đầu tiên cho giao diện
        today_date=today_date,
        user_list=user_list,
        total_users=total_users,
        total_messages=total_messages,
        total_sessions=total_sessions,
        avg_response_time=avg_response_time,
        avg_session_duration=round(avg_session_duration/60, 2),
        error_rate=error_rate,
        feedback_counts=feedback_counts,  # Không cần json.dumps()
        user_messages_data=user_messages_data,  # Không cần json.dumps()
        hourly_messages_data=hourly_messages_data,  # Không cần json.dumps()
        user_access_data=users_by_date_str,  # Không cần json.dumps()
        non_faqs_data=non_faqs_data
    )

@app.route('/api/filter_dashboard', methods=['POST'])
def filter_dashboard():
    # Nhận dữ liệu từ yêu cầu frontend
    data = request.get_json()
    user = data.get('user')
    start_date = pd.to_datetime(data.get('startDate'))
    end_date = pd.to_datetime(data.get('endDate'))
    logging.info("user: %s", user)
    logging.info("start_filter: %s", start_date)
    logging.info("end_filter: %s", end_date)
    # Fetch dữ liệu từ database
    conversation_logs_df = fetch_data_from_table('conversation_logs')
    feedback_df = fetch_data_from_table('feedback')
    session_df = fetch_data_from_table('sessions')
    users_df = fetch_data_from_table('users')

    # Loại bỏ timezone khỏi cột created_at
    conversation_logs_df['created_at'] = conversation_logs_df['created_at'].dt.tz_localize(None)
    session_df['created_at'] = session_df['created_at'].dt.tz_localize(None)
    feedback_df['created_at'] = feedback_df['created_at'].dt.tz_localize(None)
    users_df['created_at'] = users_df['created_at'].dt.tz_localize(None)
    user_list = users_df['user_id'].unique().tolist()
    # Áp dụng bộ lọc theo user và khoảng ngày
    if (user):
        conversation_logs_df = conversation_logs_df[
            (conversation_logs_df['user_id'] == user) &
            (conversation_logs_df['created_at'] >= start_date) &
            (conversation_logs_df['created_at'] <= end_date)
        ]

        feedback_df = feedback_df[
            (feedback_df['user_id'] == user) &
            (feedback_df['created_at'] >= start_date) &
            (feedback_df['created_at'] <= end_date)
        ]

        session_df = session_df[
            (session_df['user_id'] == user) &
            (session_df['created_at'] >= start_date) &
            (session_df['created_at'] <= end_date)
        ]

        users_df = users_df[
            (users_df['user_id'] == user) &
            (users_df['created_at'] >= start_date) &
            (users_df['created_at'] <= end_date)
        ]
    else:
        conversation_logs_df = conversation_logs_df[
            (conversation_logs_df['created_at'] >= start_date) &
            (conversation_logs_df['created_at'] <= end_date)
        ]

        feedback_df = feedback_df[
            (feedback_df['created_at'] >= start_date) &
            (feedback_df['created_at'] <= end_date)
        ]

        session_df = session_df[
            (session_df['created_at'] >= start_date) &
            (session_df['created_at'] <= end_date)
        ]

        users_df = users_df[
            (users_df['created_at'] >= start_date) &
            (users_df['created_at'] <= end_date)
        ]
    # Tổng hợp số liệu
    total_users = users_df['user_id'].nunique()
    total_messages = conversation_logs_df['message_id'].count()
    total_sessions = conversation_logs_df['session_id'].nunique()

    # Tính thời lượng chat trung bình
    conversation_logs_df['timestamp'] = pd.to_datetime(conversation_logs_df['timestamp'])
    conversation_logs_df['created_at'] = pd.to_datetime(conversation_logs_df['created_at'])

    # Calculate session start and end times based on the first and last message timestamps
    session_start_times = conversation_logs_df.groupby('session_id')['timestamp'].min().reset_index()
    session_start_times.columns = ['session_id', 'start_time']
    session_end_times = conversation_logs_df.groupby('session_id')['timestamp'].max().reset_index()
    session_end_times.columns = ['session_id', 'end_time']
    
    # Merge start and end times into a single DataFrame
    session_times = pd.merge(session_start_times, session_end_times, on='session_id')

    # Calculate session durations
    session_times['session_duration'] = (session_times['end_time'] - session_times['start_time']).dt.total_seconds()

    avg_session_duration = round(session_times['session_duration'].mean(), 2)

    # Tính tỷ lệ lỗi chatbot
    if total_sessions > 0:
        errored_sessions = conversation_logs_df[conversation_logs_df['outputs'].str.contains('error|fail|not found|unable', case=False)]
        error_rate = round((errored_sessions['session_id'].nunique() / total_sessions) * 100, 2)
    else:
        error_rate = 0.0  # Nếu không có session nào, tỷ lệ lỗi đặt bằng 0

    # Tính thời gian phản hồi trung bình
    conversation_logs_df['response_speed'] = (abs((conversation_logs_df['timestamp'] - conversation_logs_df['created_at']))).dt.total_seconds()
    avg_response_time = round(conversation_logs_df['response_speed'].mean(), 2)

    # Chuẩn bị dữ liệu cho biểu đồ
    user_messages_data = conversation_logs_df.groupby(conversation_logs_df['timestamp'].dt.date).size().to_dict()
    user_messages_data = {str(key): value for key, value in user_messages_data.items()}  # Chuyển datetime thành chuỗi

    hourly_messages_data = conversation_logs_df.groupby(conversation_logs_df['timestamp'].dt.hour).size().to_dict()

    # Tính tỷ lệ phản hồi người dùng
    feedback_subset = feedback_df[['message_id', 'feedback_type', 'feedback_text']]
    logging.info("Feedback Counts: %s", feedback_subset)
    conversation_logs_df_feedback = pd.merge(conversation_logs_df, feedback_subset, on='message_id', how='left')
    conversation_logs_df_feedback = conversation_logs_df_feedback.drop_duplicates(subset=['message_id'])
    # Tính toán số lượng mỗi loại feedback_type
    # Thay thế NaN bằng "No Feedback"
    conversation_logs_df_feedback['feedback_type'] = conversation_logs_df_feedback['feedback_type'].fillna('no_feedback')

    feedback_counts = conversation_logs_df_feedback['feedback_type'].value_counts().to_dict()

    # Xử lý dữ liệu người dùng theo ngày
    session_df['created_at'] = pd.to_datetime(session_df['created_at']).dt.date
    users_by_date = session_df.groupby('created_at').size().to_dict()
    users_by_date_str = {str(k): v for k, v in users_by_date.items()}  # Chuyển datetime thành chuỗi

    non_faqs_df = conversation_logs_df[conversation_logs_df['inputs'] != ""]

    # Creating the Non_FAQs_df
    non_faqs_df = non_faqs_df[['message_id', 'inputs', 'outputs', 'domain']].copy()
    non_faqs_df['usage_count'] = non_faqs_df.groupby('inputs')['inputs'].transform('count')
    non_faqs_df = non_faqs_df[['message_id', 'inputs', 'domain', 'usage_count', 'outputs']]
    non_faqs_df.columns = ['question_id', 'text_content', 'domain', 'usage_count', 'outputs']
    non_faqs_df_used = non_faqs_df[['text_content', 'usage_count', 'outputs']]

    # Sort by 'usage_count' in descending order
    non_faqs_df_used = non_faqs_df_used.sort_values(by='usage_count', ascending=False)
    non_faqs_df_used = non_faqs_df_used.drop_duplicates(subset='text_content', keep='first')
    non_faqs_data = non_faqs_df_used.to_dict(orient='records')

    response_data = {
        'user_list': user_list,  # Chuyển user_id thành chuỗi
        'total_users': int(total_users),
        'total_messages': int(total_messages),
        'total_sessions': total_sessions,
        'avg_response_time': avg_response_time,
        'avg_session_duration': round(avg_session_duration/60,2),  # Giả sử cùng cách tính
        'error_rate': error_rate,
        'feedback_counts': feedback_counts,
        'user_messages_data': user_messages_data,
        'hourly_messages_data': hourly_messages_data,
        'user_access_data': users_by_date_str,
        'non_faqs_data': non_faqs_data
    }

    # Log để kiểm tra dữ liệu JSON
    logging.info("user_list: %s", user_list)
    logging.info("total_users: %s", int(total_users))
    logging.info("total_messages: %s", total_messages)
    logging.info("total_sessions: %s", total_sessions)
    logging.info("avg_response_time: %s", avg_response_time)
    logging.info("avg_session_duration: %s", avg_session_duration)
    logging.info("error_rate: %s", error_rate)
    logging.info("feedback_counts: %s", feedback_counts)
    logging.info("user_messages_data: %s", user_messages_data)
    logging.info("hourly_messages_data: %s", hourly_messages_data)
    logging.info("user_access_data: %s", json.dumps(users_by_date_str))
    logging.info("non_faqs_data: %s", non_faqs_data)


    def log_data_types(data):
        for key, value in data.items():
            if isinstance(value, dict):
                # Log chi tiết kiểu dữ liệu bên trong dictionary
                logging.info(f"{key} (dict):")
                for sub_key, sub_value in value.items():
                    logging.info(f"  {sub_key}: {type(sub_value)}")
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Log chi tiết kiểu dữ liệu trong danh sách dictionary
                logging.info(f"{key} (list of dict):")
                for sub_key in value[0].keys():
                    logging.info(f"  {sub_key}: {type(value[0][sub_key])}")
            else:
                # Log kiểu dữ liệu thông thường
                logging.info(f"{key}: {type(value)}")

    log_data_types(response_data)

    return jsonify(response_data)

@app.errorhandler(403)
def forbidden_page(error):
    return render_template('403.html'), 403  # Trang lỗi 403

if __name__ == '__main__':
    app.run(debug=True)
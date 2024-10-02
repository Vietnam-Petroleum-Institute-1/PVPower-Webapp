from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response
import requests
import logging
from databases import update_conversation_title, get_session_from_conversation, session_continue, connect_db, user_exists, end_session, session, session_exists, conversation, insert_user, get_transcripts, add_conversation, get_conversation_id, write_feedback, upload_pending_FAQ, session_valid, error_logs, get_all_conversations
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

app = Flask(__name__)
CORS(app) 

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

@app.route('/api/check_token', methods=['POST'])
def api_check_token():
    data = request.json  # Thay đổi để lấy toàn bộ dữ liệu JSON
    token = data.get('token')
    logging.debug(f"Token received: {token}")
    user_id = decode_token(token)
    
    if user_id:
        conn = connect_db()
        session_id = session_continue(conn, user_id)
        if not session_id:
            session_id = f"{uuid.uuid4()}"
        if isinstance(session_id, tuple):
            session_id = session_id[0]
        logging.debug(f"Redirecting to home with session_id: {session_id}")
        
        # Set cookie for session_id and user_id
        expires = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        # Redirect trực tiếp về chatbot và set cookie
        response = redirect(url_for('chatbot'))
        response.set_cookie('session_id', session_id, expires=expires, path='/', samesite='Lax', secure=False) # Thêm các tùy chọn nếu cần
        response.set_cookie('user_id', user_id, expires=expires, path='/', samesite='Lax', secure=False)

        return response  # Trả về redirect luôn
    else:
        logging.warning(f"Authentication failed: Token not valid")
        return redirect(url_for('signin'))  # Nếu token không hợp lệ, chuyển về trang đăng nhập


@app.after_request
def add_security_headers(response):
    # Bỏ 'X-Frame-Options' để không hạn chế việc nhúng iframe
    response.headers.pop('X-Frame-Options', None)

    # Cho phép tất cả các domain nhúng iframe
    response.headers['Content-Security-Policy'] = "frame-ancestors *"

    # # Vô hiệu hóa bộ nhớ cache
    # response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    # response.headers["Pragma"] = "no-cache"
    # response.headers["Expires"] = "0"

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

    logging.debug(f"Rendering home page for user_id: {user_id}, session_id: {session_id}")
    return render_template('index.html')

@app.route('/chatbot')
def chatbot():
    session_id = request.cookies.get('session_id')
    user_id = request.cookies.get('user_id')

    if not session_id:
        logging.debug("No session_id found, redirecting to signin.")
        return redirect(url_for('signin'))

    logging.debug(f"Rendering home page for user_id: {user_id}, session_id: {session_id}")
    return render_template('chatbot.html')

@app.route('/chatbot_index')
def chatbot_index():
    session_id = request.cookies.get('session_id')
    user_id = request.cookies.get('user_id')

    if not session_id:
        logging.debug("No session_id found, redirecting to signin.")
        return redirect(url_for('signin'))

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
        
        if CHATBOT_URL == "http://157.66.46.53/v1":
            success = True
            message = "Thành Công!"
        else:
            success, message = authenticate_user(username, password)
            conn_db = connect_db()
            # if not user_exists(conn_db, username):
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
        error_logs(conn, user_id, session_id, conversation_id, user_message, e, "500")
        return jsonify({"result": f"Xin lỗi, tôi không đủ thông tin để trả lời câu hỏi này"}), 500
    except Exception as e:
        app.logger.error(f"Exception: {e}")
        error_logs(conn, user_id, session_id, conversation_id, user_message, e, "500")
        return jsonify({"result": f"Xin lỗi, tôi không đủ thông tin để trả lời câu hỏi này"}), 500


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
        conn.close()
        return jsonify({"conversation_id": conversation_id, "message_id": result["message_id"]})
    except requests.exceptions.RequestException as e:
        app.logger.error(f"RequestException: {e}")
        error_logs(conn, user_id, session_id, conversation_id, "", e, "501")
        return jsonify({"result": f"Xin lỗi, tôi không đủ thông tin để trả lời câu hỏi này"}), 501
    except Exception as e:
        app.logger.error(f"Exception: {e}")
        error_logs(conn, user_id, session_id, conversation_id, "", e, "501")
        return jsonify({"result": f"Xin lỗi, tôi không đủ thông tin để trả lời câu hỏi này"}), 501

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

    today = datetime.now().date()
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




if __name__ == '__main__':
    app.run(debug=True)
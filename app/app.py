from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response
import requests
import logging
from databases import connect_db, user_exists, end_session, session, session_exists, conversation, insert_user, get_message_lastest_timestamp, get_transcripts, add_conversation, get_conversation_id, bot_id_exist, write_feedback, upload_pending_FAQ, session_valid, error_logs
import json
from datetime import datetime, timedelta
import re
from flask_cors import CORS
from dotenv import load_dotenv
import os
from ldap3 import Server, Connection, ALL, SUBTREE
import uuid


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) 

# Set up logging
logging.basicConfig(level=logging.DEBUG)

load_dotenv()

CHATBOT_APIKEY = os.getenv('CHATBOT_APIKEY')
UPLOAD_APIKEY = os.getenv('UPLOAD_APIKEY')
LDAP_SERVER = os.getenv('LDAP_SERVER')
LDAP_USER = os.getenv('LDAP_USER')
LDAP_PASSWORD = os.getenv('LDAP_PASSWORD')
BASE_DN = os.getenv('BASE_DN')

def authenticate_user(username, password):
    try:
        # Nếu username chứa domain (vd: pv-power\ldap_admin), tách ra
        if '\\' in username:
            domain, username = username.split('\\', 1)

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
    return render_template('index.html', user_id=user_id, session_id=session_id)

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')


        logging.debug(f"Received POST request for signin with username: {username}")

        if not username or not password:
            logging.warning("Username or password missing.")
            return render_template('signin.html', error="Username or password is missing.")
        
        # success, message = authenticate_user(username, password)
        success = True
        message = "Thành Công!"
        if success:
            session_id = f"{uuid.uuid4()}"
            logging.debug(f"Redirecting to home with session_id: {session_id}")
            
            # Set cookie for session_id and user_id
            response = make_response(redirect(url_for('home')))
            response.set_cookie('session_id', session_id)
            response.set_cookie('user_id', username)

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

    url = 'http://157.66.46.53/v1/chat-messages'
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
        def extract_domain(input_string):
            match = re.search(r'Domain \d+', input_string)
            if match:
                return match.group(0)
            else:
                return "FAQ"
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()

        result = response.json()

        print("Result:", result)
        result_answer = decode_unicode_escapes(result["answer"])
        domain = extract_domain(result_answer)
        input_token = len(user_message)//4 + 1
        output_token = len(result)//4 + 1
        total_token = input_token + output_token
        timestamp = datetime.now()
        print(result["message_id"])
        conversation(conn, result["message_id"], session_id, user_id, "gpt", user_message, input_token, result_answer, output_token, total_token, timestamp, conversation_id, domain)
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

    url = 'http://157.66.46.53/v1/chat-messages'
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
        add_conversation(conn, conversation_id, session_id, user_id)
        conn.close()
        return jsonify({"conversation_id": conversation_id})
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
    name = request.json['name']
    bot_id = request.json['bot_id']
    if not user_exists(conn, user_id):
        if not bot_id_exist(conn, bot_id):
            return jsonify({"result": "Bot ID does not exist"}), 404
        insert_user(conn, user_id, name, bot_id)
    conn.close()
    return jsonify({"result": "User added successfully"})

@app.route('/api/user_exist', methods=['POST'])
def user_exist():
    conn = connect_db()
    user_id = request.json['user_id']
    exists, bot_id = user_exists(conn, user_id)
    if not exists:
        return jsonify({"result": 0}), 404
    conn.close()
    return jsonify({"result": 1, "bot_id": bot_id[0]})

@app.route('/api/chat_status', methods=['GET'])
def api_chat_status():
    conn = connect_db()
    data = request.get_json()
    user_id = data.get('user_id')
    session_id = data.get('session_id')
    print(f"user_id: {user_id}, session_id: {session_id}")
    
    if not user_exists(conn, user_id):
        return jsonify({"result": "User does not exist"}), 404
    if not session_exists(conn, user_id, session_id):
        return jsonify({"result": "Session does not exist"}), 404
    
    timestamp = get_message_lastest_timestamp(conn, user_id, session_id)
    print(f"timestamp: {timestamp}")
    
    if timestamp is None or len(timestamp) == 0:
        return jsonify({"result": "No message found"}), 404
    
    timestamp = timestamp[0]
    now = datetime.now()
    diff = now - timestamp
    
    if diff <= timedelta(minutes=5):
        return jsonify({"result": 1})
    else:
        return jsonify({"result": 0})
    
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
    if not session_valid(conn, user_id, session_id):
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

if __name__ == '__main__':
    app.run(debug=True)
import jwt
from datetime import datetime, timedelta

# Thông tin cần mã hóa
user_id = "phuongpd"
secret_key = "96fc0cc6-3531-435d-9279-368691964ed3"  # Khóa bí mật để mã hóa

# Thời gian hiện tại
now = datetime.utcnow()
now = now + timedelta(hours=7)

expiration_time = now + timedelta(hours=1, minutes=0)
exp_timestamp = expiration_time.timestamp()
start = now.date()

# Chuyển đổi `start` sang chuỗi để JSON có thể serializable
start_str = start.isoformat()

# Payload của token
payload = {
    'user_id': user_id,
    'exp': exp_timestamp,
    "start": start_str,  # Dùng chuỗi ISO format thay vì object datetime.date
    "session_id": "dsadassdads"
}

print(payload)

# Tạo JWT token
token = jwt.encode(payload, secret_key, algorithm='HS256')

print(f"Generated token: {token}")

# Giải mã JWT token để kiểm tra lại
token_decode = jwt.decode(token, secret_key, algorithms=['HS256'])
print("decode:", token_decode)

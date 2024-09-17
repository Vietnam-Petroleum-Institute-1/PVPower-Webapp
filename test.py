import jwt
from datetime import datetime, timedelta

# Thông tin cần mã hóa
user_id = "phuongpd"
secret_key = "secret"  # Khóa bí mật để mã hóa

# Thời gian hiện tại
now = datetime.utcnow()

# Thời điểm hết hạn (11:00:00)
expiration_time = datetime.combine(now.date(), datetime.min.time()) + timedelta(hours=18, minutes=30)
exp_timestamp = expiration_time.timestamp()

# Payload của token
payload = {
    'user_id': user_id,
    'exp': exp_timestamp
}

# Tạo JWT token
token = jwt.encode(payload, "96fc0cc6-3531-435d-9279-368691964ed3", algorithm='HS256')

print(f"Generated token: {token}")

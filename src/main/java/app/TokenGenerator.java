package app;

import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;

import java.util.Date;

public class TokenGenerator {
    public static void main(String[] args) {
        // Thông tin cần mã hóa
        String userId = "phuongpd";
        String secretKey = "96fc0cc6-3531-435d-9279-368691964ed3";  // Khóa bí mật để mã hóa

        // Tạo thời gian hiện tại
        long nowMillis = System.currentTimeMillis();
        Date now = new Date(nowMillis);
        
        // Tính toán thời gian hết hạn (24 giờ sau)
        Date expiration = new Date(nowMillis + 24 * 60 * 60 * 1000);  // 24 giờ
        
        // Tạo token
        Algorithm algorithm = Algorithm.HMAC256(secretKey);
        String token = JWT.create()
                .withClaim("user_id", userId)
                .withClaim("start", now.toInstant().toString())  // Dùng chuỗi ISO 8601
                .withClaim("session_id", "abcxyz")
                .withExpiresAt(expiration)
                .sign(algorithm);
        
        // In token ra màn hình
        System.out.println("Generated token: " + token);
    }
}

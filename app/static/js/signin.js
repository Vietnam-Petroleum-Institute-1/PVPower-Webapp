document.getElementById('signinForm').addEventListener('submit', function(event) {
    event.preventDefault();  // Ngăn chặn hành động mặc định để kiểm tra tính hợp lệ

    // Lấy các giá trị từ các trường nhập liệu
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();

    // Kiểm tra tính hợp lệ của dữ liệu nhập
    if (!username || !password) {
        alert('Username and Password are required.');
    } else {
        this.submit();  // Nếu hợp lệ, submit form và để Flask xử lý
    }
});

const params = new URLSearchParams(window.location.search);
const token = params.get("token");

if (token) {
  console.log("Token found in URL:", token);

  // Gọi API /api/check_token với token từ URL
  fetch("/api/check_token", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ token: token }),
  }).then(response => {
    if (response.redirected) {
      // Server sẽ trả về redirect nếu token hợp lệ hoặc không hợp lệ
      window.location.href = response.url;
    }
  }).catch(error => {
    console.error("Error in token verification", error);
  });
}

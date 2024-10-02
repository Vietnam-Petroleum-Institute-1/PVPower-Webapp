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
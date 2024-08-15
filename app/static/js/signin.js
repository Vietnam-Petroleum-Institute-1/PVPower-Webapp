document.getElementById('signinForm').addEventListener('submit', function(event) {
    // Ngăn chặn form gửi đi để kiểm tra tính hợp lệ
    event.preventDefault();

    // Lấy các giá trị từ các trường nhập liệu
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();

    // Tham chiếu đến thẻ hiển thị lỗi
    const errorMessage = document.getElementById('error-message');
    
    // Kiểm tra tính hợp lệ của dữ liệu nhập
    if (!username || !password) {
        errorMessage.textContent = 'Username and Password are required.';
        errorMessage.style.display = 'block';
    } else {
        errorMessage.style.display = 'none';
        // Nếu hợp lệ, submit form (có thể gửi dữ liệu đến server bằng AJAX nếu cần)
        alert('Form submitted successfully!');
        // Uncomment the line below if you want to proceed with form submission
        // this.submit();
    }
});

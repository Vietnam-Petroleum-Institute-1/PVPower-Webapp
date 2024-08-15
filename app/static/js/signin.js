function validateSignInForm() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('error');

    if (username === '' || password === '') {
        errorDiv.textContent = 'Please fill out both fields.';
        return false;
    }

    return true;
}

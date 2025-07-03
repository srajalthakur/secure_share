// Basic frontend logic for Secure Share
const loginSection = document.getElementById('login-section');
const mainSection = document.getElementById('main-section');
const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');
const userRoleSpan = document.getElementById('user-role');
const logoutBtn = document.getElementById('logout-btn');
const uploadForm = document.getElementById('upload-form');
const fileInput = document.getElementById('file-input');
const uploadSuccess = document.getElementById('upload-success');
const fileList = document.getElementById('file-list');

let token = null;
let userRole = null;

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    loginError.style.display = 'none';
    // JWT login
    const res = await fetch('/api/token/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    if (res.ok) {
        const data = await res.json();
        token = data.access;
        // Get user info (role)
        const userRes = await fetch('/api/user-info/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (userRes.ok) {
            const userData = await userRes.json();
            userRole = userData.is_ops ? 'Ops User' : (userData.is_client ? 'Client User' : 'User');
            userRoleSpan.textContent = userRole;
            loginSection.style.display = 'none';
            mainSection.style.display = '';
            loadFiles();
        } else {
            loginError.textContent = 'Failed to fetch user info.';
            loginError.style.display = '';
        }
    } else {
        loginError.textContent = 'Invalid username or password.';
        loginError.style.display = '';
    }
});

logoutBtn.addEventListener('click', () => {
    token = null;
    userRole = null;
    loginSection.style.display = '';
    mainSection.style.display = 'none';
});

uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!token) return;
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    const res = await fetch('/api/upload/', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });
    if (res.ok) {
        uploadSuccess.textContent = 'File uploaded successfully!';
        uploadSuccess.style.display = '';
        loadFiles();
    } else {
        uploadSuccess.textContent = 'File upload failed.';
        uploadSuccess.style.display = '';
    }
});

async function loadFiles() {
    if (!token) return;
    const res = await fetch('/api/files/', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    fileList.innerHTML = '';
    if (res.ok) {
        const files = await res.json();
        files.forEach(f => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';
            li.textContent = f.file;
            const downloadBtn = document.createElement('a');
            downloadBtn.href = `/api/download/${f.id}/`;
            downloadBtn.textContent = 'Download';
            downloadBtn.className = 'btn btn-sm btn-primary';
            downloadBtn.target = '_blank';
            li.appendChild(downloadBtn);
            fileList.appendChild(li);
        });
    } else {
        fileList.innerHTML = '<li class="list-group-item">Failed to load files.</li>';
    }
}

const USER_SERVICE_URL = 'http://localhost:5001';
const CATALOG_SERVICE_URL = 'http://localhost:5002';
let currentToken = '';

//Utility Functions

function setToken(token) {
    currentToken = token;
    localStorage.setItem('jwtToken', token);
    document.getElementById('token-display').textContent = `JWT Token: ${token.substring(0, 30)}...`;
    
    // Enable buttons when logged in
    document.querySelectorAll('section button').forEach(btn => btn.disabled = false);
}

function clearToken() {
    currentToken = '';
    localStorage.removeItem('jwtToken');
    document.getElementById('token-display').textContent = 'JWT Token: (Not logged in)';
    
    // Disable buttons when logged out
    document.querySelectorAll('section button').forEach(btn => {
        if (btn.textContent !== 'Login') btn.disabled = true;
    });
}

// Check for token on page load
window.onload = () => {
    const storedToken = localStorage.getItem('jwtToken');
    if (storedToken) {
        setToken(storedToken);
        document.getElementById('login-status').textContent = "Logged in with stored token.";
    } else {
        clearToken();
    }
};

// API Handlers
async function handleLogin() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const statusEl = document.getElementById('login-status');
    statusEl.textContent = 'Logging in...';

    try {
        const response = await fetch(`${USER_SERVICE_URL}/users/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            setToken(data.token);
            statusEl.textContent = 'Login successful!';
        } else {
            clearToken();
            statusEl.textContent = `Login failed: ${data.message || 'Check credentials'}`;
        }
    } catch (error) {
        statusEl.textContent = 'Error: Could not reach User Service.';
        clearToken();
    }
}

async function handleCreateRecipe() {
    if (!currentToken) {
        document.getElementById('recipe-status').textContent = 'Error: Please log in first.';
        return;
    }

    const title = document.getElementById('recipe-title').value;
    const instructions = document.getElementById('recipe-instructions').value;
    const imageFile = document.getElementById('recipe-image').files[0];
    const statusEl = document.getElementById('recipe-status');
    statusEl.textContent = 'Creating recipe...';

    // Use FormData for file uploads (replaces JSON)
    const formData = new FormData();
    formData.append('title', title);
    formData.append('instructions', instructions);
    
    if (imageFile) {
        formData.append('image', imageFile, imageFile.name);
    }

    try {
        const response = await fetch(`${CATALOG_SERVICE_URL}/recipes`, {
            method: 'POST',
            headers: {
                // IMPORTANT: The browser sets 'Content-Type: multipart/form-data' automatically for FormData
                'Authorization': `Bearer ${currentToken}`
            },
            // The body is the FormData object itself
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            statusEl.textContent = `Recipe created! ID: ${data.id}. Image saved to: ${data.image_url}`;
        } else if (response.status === 401) {
            statusEl.textContent = 'Error: Unauthorized (Token Expired or Invalid). Please log in again.';
            clearToken();
        } else {
            statusEl.textContent = `Error creating recipe: ${data.message || 'Check server logs'}`;
        }
    } catch (error) {
        statusEl.textContent = 'Error: Could not reach Catalog Service.';
    }
}


async function handleGetRecipes() {
    if (!currentToken) {
        document.getElementById('recipe-status').textContent = 'Error: Please log in first.';
        return;
    }

    const listEl = document.getElementById('recipe-list');
    listEl.innerHTML = '<li>Fetching...</li>';

    try {
        const response = await fetch(`${CATALOG_SERVICE_URL}/recipes`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${currentToken}`
            }
        });

        const data = await response.json();
        listEl.innerHTML = ''; // Clear fetching message

        if (response.ok) {
            if (data.length === 0) {
                listEl.innerHTML = '<li>No recipes found.</li>';
            } else {
                data.forEach(recipe => {
                    const listItem = document.createElement('li');
                    listItem.innerHTML = `<strong>${recipe.title}</strong> (Image URL: ${recipe.image_url || 'None'})`;
                    listEl.appendChild(listItem);
                });
            }
        } else {
            listEl.innerHTML = `<li>Error: ${data.message || 'Failed to fetch recipes.'}</li>`;
        }
    } catch (error) {
        listEl.innerHTML = '<li>Error: Could not reach Catalog Service.</li>';
    }
}

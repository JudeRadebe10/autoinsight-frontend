// ─────────────────────────────────────────────────────────────
//  AutoInsight ZA – Global Authentication & Navbar Integrator
// ─────────────────────────────────────────────────────────────

const BACKEND_API = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://127.0.0.1:8765'
  : 'https://autoinsight-backend-wp42.onrender.com';

// Globally exposed helper to log out
function logoutUser() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_role');
  localStorage.removeItem('user_email');
  localStorage.removeItem('user_name');
  window.location.href = 'index.html';
}

// Dynamically integrate auth states with existing page elements
async function checkAuthAndPopulateNavbar() {
  const token = localStorage.getItem('access_token');
  if (!token) return;

  try {
    const response = await fetch(`${BACKEND_API}/api/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.status === 401 || response.status === 403) {
      // Token is invalid/expired
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_role');
      return;
    }

    if (!response.ok) return;

    const userData = await response.json();
    
    // Save user detail state for custom settings access
    localStorage.setItem('user_role', userData.roles[0] || 'client');
    localStorage.setItem('user_email', userData.email);
    localStorage.setItem('user_name', userData.full_name || 'Client');
    if (userData.settings && userData.settings.theme) {
      localStorage.setItem('user_theme', userData.settings.theme);
      // Apply persisted theme immediately
      if (userData.settings.theme === 'dark') {
        document.body.classList.add('dark-theme');
      } else {
        document.body.classList.remove('dark-theme');
      }
    }

    // Dynamic navbar rewrite to show Settings + Sign Out
    updateNavbarToAuthenticated(userData);
  } catch (error) {
    console.error('Error during global auth verification:', error);
  }
}

function updateNavbarToAuthenticated(user) {
  const primaryRole = user.roles[0] || 'client';
  
  // Create beautiful premium replacements
  const desktopMarkup = `
    <div style="display:flex;align-items:center;gap:12px">
      <a href="settings.html" class="btn btn-secondary btn-sm" style="display:inline-flex;align-items:center;gap:6px">
        <i class="fas fa-cog"></i> Settings
      </a>
      ${primaryRole === 'super_admin' || primaryRole === 'admin' ? `
        <span style="background:rgba(0,71,255,0.15);color:var(--accent);font-size:11px;font-weight:700;padding:4px 8px;border-radius:6px;border:1px solid rgba(0,71,255,0.3)">
          ${primaryRole.toUpperCase()}
        </span>
      ` : ''}
      <button onclick="logoutUser()" class="btn btn-ghost btn-sm" style="color:var(--muted);border:1px solid var(--border);padding:6px 12px;border-radius:var(--r-sm);cursor:pointer;font-weight:600;font-size:12.5px;transition:all var(--t)">
        <i class="fas fa-sign-out-alt"></i> Sign Out
      </button>
    </div>
  `;

  const userName = user.full_name || user.email.split('@')[0];

  const mobileMarkup = `
    <div style="padding: 12px 16px; background: rgba(0,71,255,0.05); border-radius: var(--r-sm); margin-bottom: 12px; text-align: center; border: 1px solid rgba(0,71,255,0.1);">
      <span style="font-size: 12px; color: var(--muted); font-weight: 500;">Signed in as</span><br>
      <strong style="color: var(--ink); font-size: 15px; display: inline-flex; align-items: center; gap: 6px; margin-top: 2px;">
        <i class="fas fa-user-circle" style="color: var(--accent);"></i> ${userName}
      </strong>
      ${primaryRole === 'super_admin' || primaryRole === 'admin' ? `
        <span style="display:inline-block; margin-top:6px; background:var(--accent); color:#fff; font-size:10px; padding:3px 8px; border-radius:6px; font-weight:700; letter-spacing:0.5px;">${primaryRole.toUpperCase()}</span>
      ` : ''}
    </div>
    <div style="display:flex; gap:8px;">
      <a href="settings.html" class="btn btn-secondary btn-sm" style="flex:1;justify-content:center;gap:6px">
        <i class="fas fa-cog"></i> Settings
      </a>
      <button onclick="logoutUser()" class="btn btn-secondary btn-sm" style="flex:1;justify-content:center;background:none;border:1.5px solid var(--border);color:var(--muted);gap:6px">
        <i class="fas fa-sign-out-alt"></i> Sign Out
      </button>
    </div>
    <div style="display:flex; margin-top: 8px;">
      <a href="estimator.html" class="btn btn-primary btn-sm" style="flex:1;justify-content:center;gap:6px">
        <i class="fas fa-calculator"></i> Get Fair Value
      </a>
    </div>
  `;

  // Desktop Navbar Integration
  const desktopNavRight = document.querySelector('.nav-right');
  if (desktopNavRight) {
    // Find the Sign In link (which points to login.html)
    const signInBtn = desktopNavRight.querySelector('a[href="login.html"]');
    if (signInBtn) {
      // Replace only the Sign In button, keeping target estimator button
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = desktopMarkup.trim();
      desktopNavRight.replaceChild(tempDiv.firstChild, signInBtn);
    }
  }

  // Mobile Navbar Integration
  const mobileNavActions = document.querySelector('.mobile-nav-actions');
  if (mobileNavActions) {
    mobileNavActions.innerHTML = mobileMarkup;
  }
}

// Run check globally on page load
document.addEventListener('DOMContentLoaded', () => {
  checkAuthAndPopulateNavbar();
});

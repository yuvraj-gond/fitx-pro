// =============================================================================
// frontend/assets/js/shell.js
// Injects the sidebar + topbar into every app page
// =============================================================================

function buildShell(activePage, pageTitle) {
  if (!requireAuth()) return;

  const user = Auth.getUser() || {};
  const initials = (user.username || 'U').charAt(0).toUpperCase();

  const navItems = [
    { id: 'dashboard', icon: '📊', label: 'Dashboard',    href: 'dashboard.html' },
    { id: 'nutrition', icon: '🥗', label: 'Nutrition',    href: 'nutrition.html' },
    { id: 'workout',   icon: '🏋️', label: 'Workout',      href: 'workout.html'   },
    { id: 'insights',  icon: '🤖', label: 'AI Insights',  href: 'insights.html'  },
    { id: 'body',      icon: '📏', label: 'Body Metrics',  href: 'body.html'      },
    { id: 'profile',   icon: '👤', label: 'Profile',       href: 'profile.html'   },
  ];

  const navHTML = navItems.map(n => {
    const active  = n.id === activePage ? 'active' : '';
    return `<a class="nav-item ${active}" href="${n.href}" id="nav-${n.id}">
      <span class="nav-icon">${n.icon}</span>
      <span>${n.label}</span>
    </a>`;
  }).join('');

  const sidebarHTML = `
  <nav class="sidebar" id="sidebar">
    <div class="sidebar-logo">
      <div class="wordmark">💪 FITX PRO</div>
      <div class="tagline">AI Fitness Tracker</div>
    </div>
    <div class="sidebar-user">
      <div class="user-avatar">${initials}</div>
      <div class="user-info">
        <div class="user-name">${user.username || 'User'}</div>
      </div>
    </div>
    <div class="sidebar-nav">
      <div class="label section-label">Navigation</div>
      ${navHTML}
    </div>
    <div class="sidebar-footer">
      <button class="logout-btn" onclick="logout()">
        <span>🚪</span> Sign Out
      </button>
    </div>
  </nav>`;

  const topbarHTML = `
  <header class="topbar">
    <div style="display:flex;align-items:center;gap:.9rem;">
      <button class="hamburger" onclick="toggleSidebar()" aria-label="Toggle menu">☰</button>
      <span class="topbar-title">${pageTitle}</span>
    </div>
    <div class="topbar-actions">
      <span id="topbar-date" style="font-size:.78rem;color:var(--text-2);"></span>
    </div>
  </header>`;

  const shell = document.querySelector('.app-shell');
  shell.insertAdjacentHTML('afterbegin', sidebarHTML);
  const mainContent = shell.querySelector('.main-content');
  mainContent.insertAdjacentHTML('afterbegin', topbarHTML);

  // Date display
  document.getElementById('topbar-date').textContent =
    new Date().toLocaleDateString('en-GB', { weekday:'short', day:'numeric', month:'short', year:'numeric' });

  // Mobile overlay
  const overlay = document.createElement('div');
  overlay.id = 'sidebar-overlay';
  overlay.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:99;backdrop-filter:blur(2px);';
  overlay.onclick = () => toggleSidebar(false);
  document.body.appendChild(overlay);

  // Mobile Bottom Nav
  const bottomNavHTML = `
  <nav class="bottom-nav">
    ${navItems.slice(0, 5).map(n => `
      <a class="bottom-nav-item ${n.id === activePage ? 'active' : ''}" href="${n.href}">
        <div class="icon">${n.icon}</div>
        <div class="label">${n.label}</div>
      </a>
    `).join('')}
  </nav>`;
  document.body.insertAdjacentHTML('beforeend', bottomNavHTML);
}

function toggleSidebar(force) {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  const isOpen  = sidebar.classList.contains('open');
  const open    = force !== undefined ? force : !isOpen;
  sidebar.classList.toggle('open', open);
  overlay.style.display = open ? 'block' : 'none';
}

function logout() {
  Auth.clear();
  window.location.href = 'login.html';
}

if ('serviceWorker' in navigator) { window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js')); }

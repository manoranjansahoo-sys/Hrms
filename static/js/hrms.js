// Enterprise HRMS JavaScript Suite

document.addEventListener('DOMContentLoaded', function () {
    // 1. Live Clock
    function updateClock() {
        const clockEls = document.querySelectorAll('.live-clock-display');
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
        const dateStr = now.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });

        clockEls.forEach(el => {
            el.innerHTML = `<span class="time-part">${timeStr}</span> <span class="text-muted small ms-2">${dateStr}</span>`;
        });
    }

    if (document.querySelector('.live-clock-display')) {
        updateClock();
        setInterval(updateClock, 1000);
    }

    // 2. Theme Toggle (Light / Dark)
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const htmlEl = document.documentElement;

    const savedTheme = localStorage.getItem('hrms_theme') || 'light';
    htmlEl.setAttribute('data-bs-theme', savedTheme);
    updateThemeIcon(savedTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function () {
            const currentTheme = htmlEl.getAttribute('data-bs-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            htmlEl.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('hrms_theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }

    function updateThemeIcon(theme) {
        if (!themeToggleBtn) return;
        const icon = themeToggleBtn.querySelector('i');
        if (icon) {
            if (theme === 'dark') {
                icon.className = 'bi bi-sun-fill text-warning';
            } else {
                icon.className = 'bi bi-moon-stars text-secondary';
            }
        }
    }

    // 3. Mobile Sidebar Toggle & Close Controls
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
    const sidebar = document.querySelector('.sidebar');

    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove('show');
        const backdrop = document.querySelector('.sidebar-backdrop');
        if (backdrop) backdrop.remove();
    }

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('show');
            let backdrop = document.querySelector('.sidebar-backdrop');
            if (sidebar.classList.contains('show')) {
                if (!backdrop) {
                    backdrop = document.createElement('div');
                    backdrop.className = 'sidebar-backdrop';
                    document.body.appendChild(backdrop);
                    backdrop.addEventListener('click', closeSidebar);
                }
            } else if (backdrop) {
                backdrop.remove();
            }
        });
    }

    if (sidebarCloseBtn) {
        sidebarCloseBtn.addEventListener('click', closeSidebar);
    }

    // Dismiss sidebar with ESC key on mobile/tablet
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && sidebar && sidebar.classList.contains('show')) {
            closeSidebar();
        }
    });

    // 4. Auto dismiss alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 6000);
    });
});


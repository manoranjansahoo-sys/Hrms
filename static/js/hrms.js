// Enterprise HRMS JavaScript Suite

document.addEventListener('DOMContentLoaded', function () {
    // Theme Toggle (Light / Dark)
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
                icon.className = 'bi bi-sun';
            } else {
                icon.className = 'bi bi-moon-stars';
            }
        }
    }

    // Mobile Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');

    if (sidebarToggle && sidebar) {
        const desktopLayout = window.matchMedia('(min-width: 992px)');
        const sidebarMenu = sidebar.querySelector('.sidebar-menu');
        const backdrop = document.createElement('div');
        backdrop.className = 'sidebar-backdrop';

        // A fixed sidebar does not reliably pass vertical wheel input to the page at its edges.
        sidebarMenu.addEventListener('wheel', function (event) {
            if (!desktopLayout.matches || !event.cancelable || event.ctrlKey || event.shiftKey) return;

            const deltaMode = event.deltaMode;
            const { deltaX, deltaY } = event;
            if (Math.abs(deltaY) <= Math.abs(deltaX)) return;

            const remaining = sidebarMenu.scrollHeight - sidebarMenu.clientHeight - sidebarMenu.scrollTop;
            if (deltaY > 0 ? remaining > 1 : sidebarMenu.scrollTop > 0) return;

            event.preventDefault();
            const page = document.scrollingElement;
            let pixels = deltaY;
            if (deltaMode === WheelEvent.DOM_DELTA_LINE) {
                pixels *= parseFloat(getComputedStyle(sidebarMenu).lineHeight) || 16;
            } else if (deltaMode === WheelEvent.DOM_DELTA_PAGE) {
                pixels *= page.clientHeight;
            }
            page.scrollBy({ top: pixels, behavior: 'instant' });
        }, { passive: false });

        function closeSidebar() {
            sidebar.classList.remove('show');
            sidebarToggle.setAttribute('aria-expanded', 'false');
            backdrop.remove();
        }

        sidebarToggle.addEventListener('click', function () {
            if (sidebar.classList.contains('show')) {
                closeSidebar();
                return;
            }

            sidebar.classList.add('show');
            sidebarToggle.setAttribute('aria-expanded', 'true');
            document.body.appendChild(backdrop);
            sidebarMenu.focus({ preventScroll: true });
        });

        backdrop.addEventListener('click', function () {
            closeSidebar();
            sidebarToggle.focus({ preventScroll: true });
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && sidebar.classList.contains('show')) {
                closeSidebar();
                sidebarToggle.focus({ preventScroll: true });
            }
        });

        desktopLayout.addEventListener('change', function (event) {
            if (event.matches) closeSidebar();
        });
    }

    // Auto dismiss alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 6000);
    });
});


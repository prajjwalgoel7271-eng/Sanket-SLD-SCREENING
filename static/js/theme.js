/* Sanket Theme Switcher (Dark / Light Mode) */
(function() {
    const savedTheme = localStorage.getItem('sanket_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    document.addEventListener('DOMContentLoaded', () => {
        const toggleBtn = document.getElementById('theme-toggle-btn');
        if (toggleBtn) {
            updateToggleBtnUI(savedTheme);
            toggleBtn.addEventListener('click', () => {
                const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                document.documentElement.setAttribute('data-theme', newTheme);
                localStorage.setItem('sanket_theme', newTheme);
                updateToggleBtnUI(newTheme);
            });
        }
    });

    function updateToggleBtnUI(theme) {
        const toggleBtn = document.getElementById('theme-toggle-btn');
        if (!toggleBtn) return;
        if (theme === 'light') {
            toggleBtn.innerHTML = '🌙 Dark Mode';
        } else {
            toggleBtn.innerHTML = '☀️ Light Mode';
        }
    }
})();

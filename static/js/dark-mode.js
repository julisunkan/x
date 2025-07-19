// Dark mode functionality for DigitalSkeletonCoin (DSC) Platform

class DarkModeManager {
    constructor() {
        this.storageKey = 'digitalskeletoncoin-theme';
        this.themeToggleBtn = null;
        this.themeIcon = null;
        this.currentTheme = 'dark'; // Default theme
        this.init();
    }

    init() {
        this.initializeElements();
        this.loadSavedTheme();
        this.setupEventListeners();
        this.applyTheme(this.currentTheme);
    }

    initializeElements() {
        this.themeToggleBtn = document.getElementById('theme-toggle');
        this.themeIcon = document.getElementById('theme-icon');
        
        // If elements don't exist, create them
        if (!this.themeToggleBtn) {
            this.createThemeToggle();
        }
    }

    createThemeToggle() {
        // Create theme toggle button if it doesn't exist
        const navbar = document.querySelector('.navbar-nav');
        if (navbar) {
            const themeToggleContainer = document.createElement('li');
            themeToggleContainer.className = 'nav-item me-2';
            
            themeToggleContainer.innerHTML = `
                <button class="btn btn-outline-light btn-sm" id="theme-toggle">
                    <i class="fas fa-moon" id="theme-icon"></i>
                </button>
            `;
            
            navbar.insertBefore(themeToggleContainer, navbar.lastElementChild);
            
            this.themeToggleBtn = document.getElementById('theme-toggle');
            this.themeIcon = document.getElementById('theme-icon');
        }
    }

    setupEventListeners() {
        if (this.themeToggleBtn) {
            this.themeToggleBtn.addEventListener('click', () => {
                this.toggleTheme();
            });
        }

        // Listen for system theme changes
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', (e) => {
                // Only auto-switch if user hasn't manually set a preference
                if (!localStorage.getItem(this.storageKey)) {
                    this.applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }

        // Keyboard shortcut (Ctrl + Shift + D)
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'D') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
    }

    loadSavedTheme() {
        const savedTheme = localStorage.getItem(this.storageKey);
        
        if (savedTheme) {
            this.currentTheme = savedTheme;
        } else {
            // Detect system preference
            this.currentTheme = this.getSystemTheme();
        }
    }

    getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    setTheme(theme) {
        this.currentTheme = theme;
        this.applyTheme(theme);
        this.saveTheme(theme);
        this.updateToggleButton();
        this.announceThemeChange(theme);
    }

    applyTheme(theme) {
        const html = document.documentElement;
        const body = document.body;
        
        // Set Bootstrap theme attribute
        html.setAttribute('data-bs-theme', theme);
        
        // Add theme class to body for custom styling
        body.classList.remove('theme-light', 'theme-dark');
        body.classList.add(`theme-${theme}`);
        
        // Update meta theme-color for mobile browsers
        this.updateMetaThemeColor(theme);
        
        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: theme }
        }));
    }

    updateMetaThemeColor(theme) {
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }
        
        // Set appropriate theme color
        const themeColors = {
            dark: '#0d1117',
            light: '#ffffff'
        };
        
        metaThemeColor.content = themeColors[theme] || themeColors.dark;
    }

    updateToggleButton() {
        if (!this.themeIcon) return;
        
        // Update icon based on current theme
        if (this.currentTheme === 'dark') {
            this.themeIcon.className = 'fas fa-sun';
            if (this.themeToggleBtn) {
                this.themeToggleBtn.title = 'Switch to light mode';
                this.themeToggleBtn.setAttribute('aria-label', 'Switch to light mode');
            }
        } else {
            this.themeIcon.className = 'fas fa-moon';
            if (this.themeToggleBtn) {
                this.themeToggleBtn.title = 'Switch to dark mode';
                this.themeToggleBtn.setAttribute('aria-label', 'Switch to dark mode');
            }
        }
        
        // Add animation class
        this.themeIcon.classList.add('theme-transition');
        setTimeout(() => {
            this.themeIcon.classList.remove('theme-transition');
        }, 300);
    }

    saveTheme(theme) {
        try {
            localStorage.setItem(this.storageKey, theme);
        } catch (error) {
            console.warn('Failed to save theme preference:', error);
        }
    }

    announceThemeChange(theme) {
        // For screen readers
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = `Switched to ${theme} mode`;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
        
        // Visual feedback
        this.showThemeNotification(theme);
    }

    showThemeNotification(theme) {
        const notification = document.createElement('div');
        notification.className = 'theme-notification';
        notification.innerHTML = `
            <i class="fas fa-${theme === 'dark' ? 'moon' : 'sun'} me-2"></i>
            ${theme.charAt(0).toUpperCase() + theme.slice(1)} mode activated
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--bs-primary);
            color: white;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            z-index: 9999;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
            font-size: 0.875rem;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        // Animate out and remove
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 2000);
    }

    // Public methods for external use
    getCurrentTheme() {
        return this.currentTheme;
    }

    isDarkMode() {
        return this.currentTheme === 'dark';
    }

    isLightMode() {
        return this.currentTheme === 'light';
    }

    // Method to programmatically set theme
    setDarkMode() {
        this.setTheme('dark');
    }

    setLightMode() {
        this.setTheme('light');
    }

    // Reset to system preference
    resetToSystemTheme() {
        localStorage.removeItem(this.storageKey);
        const systemTheme = this.getSystemTheme();
        this.setTheme(systemTheme);
    }
}

// Initialize dark mode manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.darkModeManager = new DarkModeManager();
});

// CSS for theme transition animation
const themeTransitionCSS = `
.theme-transition {
    animation: themeIconSpin 0.3s ease-in-out;
}

@keyframes themeIconSpin {
    0% { transform: rotate(0deg) scale(1); }
    50% { transform: rotate(180deg) scale(1.1); }
    100% { transform: rotate(360deg) scale(1); }
}

/* Smooth transitions for theme changes */
* {
    transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}

/* Disable transitions during theme change to prevent flash */
.theme-changing * {
    transition: none !important;
}

/* Theme-specific enhancements */
.theme-dark {
    --theme-bg-primary: #0d1117;
    --theme-bg-secondary: #21262d;
    --theme-text-primary: #e6edf3;
    --theme-text-secondary: #7d8590;
}

.theme-light {
    --theme-bg-primary: #ffffff;
    --theme-bg-secondary: #f8f9fa;
    --theme-text-primary: #212529;
    --theme-text-secondary: #6c757d;
}

/* Custom scrollbar theming */
.theme-dark ::-webkit-scrollbar-track {
    background: var(--bs-gray-800);
}

.theme-dark ::-webkit-scrollbar-thumb {
    background: var(--bs-gray-600);
}

.theme-light ::-webkit-scrollbar-track {
    background: var(--bs-gray-200);
}

.theme-light ::-webkit-scrollbar-thumb {
    background: var(--bs-gray-400);
}
`;

// Inject theme transition CSS
const style = document.createElement('style');
style.textContent = themeTransitionCSS;
document.head.appendChild(style);

// Global functions for external use
window.toggleTheme = function() {
    if (window.darkModeManager) {
        window.darkModeManager.toggleTheme();
    }
};

window.setDarkMode = function() {
    if (window.darkModeManager) {
        window.darkModeManager.setDarkMode();
    }
};

window.setLightMode = function() {
    if (window.darkModeManager) {
        window.darkModeManager.setLightMode();
    }
};

// Listen for theme preference changes and update accordingly
window.addEventListener('storage', (e) => {
    if (e.key === 'digitalskeletoncoin-theme' && window.darkModeManager) {
        window.darkModeManager.loadSavedTheme();
        window.darkModeManager.applyTheme(window.darkModeManager.currentTheme);
        window.darkModeManager.updateToggleButton();
    }
});

// Export for modules/testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DarkModeManager;
}

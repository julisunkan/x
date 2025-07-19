// DigitalSkeletonCoin (DSC) App JavaScript
class DigitalSkeletonCoinApp {
    constructor() {
        this.init();
    }

    init() {
        this.initTooltips();
        this.initSidebar();
        this.initMobileResponsive();
        this.initPWAFeatures();
        this.initSidebarState();
    }

    initTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    initSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        const toggleBtn = document.querySelector('.sidebar-toggle');
        const collapseBtn = document.getElementById('sidebar-collapse-btn');
        
        // Set active navigation link
        this.setActiveNavLink();
        
        // Handle sidebar toggle (mobile)
        if (toggleBtn) {
            toggleBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleSidebar();
            });
        }
        
        // Handle sidebar collapse (desktop)
        if (collapseBtn) {
            collapseBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleSidebarCollapse();
            });
        }
        
        // Handle overlay click
        if (overlay) {
            overlay.addEventListener('click', () => {
                this.closeSidebar();
            });
        }
        
        // Close sidebar on nav link click (mobile)
        document.querySelectorAll('.sidebar .nav-link').forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth < 992) {
                    this.closeSidebar();
                }
            });
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth < 992) {
                const sidebar = document.getElementById('sidebar');
                const toggleBtn = document.querySelector('.sidebar-toggle');
                
                if (sidebar && sidebar.classList.contains('active')) {
                    if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                        this.closeSidebar();
                    }
                }
            }
        });
    }

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        
        if (sidebar && overlay) {
            const isActive = sidebar.classList.contains('active');
            
            if (isActive) {
                this.closeSidebar();
            } else {
                this.openSidebar();
            }
        }
    }

    openSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        const hamburgerMenu = document.querySelector('.hamburger-menu');
        
        if (sidebar && overlay) {
            sidebar.classList.add('active');
            overlay.classList.add('active');
            
            // Animate hamburger menu
            if (hamburgerMenu) {
                hamburgerMenu.classList.add('active');
            }
            
            document.body.style.overflow = 'hidden'; // Prevent scroll on mobile
        }
    }

    closeSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        const hamburgerMenu = document.querySelector('.hamburger-menu');
        
        if (sidebar && overlay) {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
            
            // Reset hamburger menu
            if (hamburgerMenu) {
                hamburgerMenu.classList.remove('active');
            }
            
            document.body.style.overflow = ''; // Restore scroll
        }
    }

    toggleSidebarCollapse() {
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.querySelector('.main-content');
        const footer = document.querySelector('.app-footer');
        const collapseBtn = document.getElementById('sidebar-collapse-btn');
        const collapseIcon = collapseBtn.querySelector('i');
        
        if (sidebar && mainContent) {
            const isCollapsed = sidebar.classList.contains('collapsed');
            
            if (isCollapsed) {
                // Expand sidebar
                sidebar.classList.remove('collapsed');
                mainContent.classList.remove('sidebar-collapsed');
                if (footer) footer.classList.remove('sidebar-collapsed');
                collapseIcon.className = 'fas fa-chevron-left';
                
                // Store preference
                localStorage.setItem('sidebarCollapsed', 'false');
            } else {
                // Collapse sidebar
                sidebar.classList.add('collapsed');
                mainContent.classList.add('sidebar-collapsed');
                if (footer) footer.classList.add('sidebar-collapsed');
                collapseIcon.className = 'fas fa-chevron-right';
                
                // Store preference
                localStorage.setItem('sidebarCollapsed', 'true');
            }
        }
    }

    initSidebarState() {
        // Restore sidebar state from localStorage
        const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        
        if (sidebarCollapsed && window.innerWidth >= 992) {
            const sidebar = document.getElementById('sidebar');
            const mainContent = document.querySelector('.main-content');
            const footer = document.querySelector('.app-footer');
            const collapseBtn = document.getElementById('sidebar-collapse-btn');
            const collapseIcon = collapseBtn.querySelector('i');
            
            if (sidebar && mainContent) {
                sidebar.classList.add('collapsed');
                mainContent.classList.add('sidebar-collapsed');
                if (footer) footer.classList.add('sidebar-collapsed');
                collapseIcon.className = 'fas fa-chevron-right';
            }
        }
    }

    setActiveNavLink() {
        const currentPath = window.location.pathname;
        document.querySelectorAll('.sidebar .nav-link').forEach(link => {
            const href = link.getAttribute('href');
            if (href === currentPath) {
                link.classList.add('active');
            }
        });
    }

    initMobileResponsive() {
        // Handle window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth >= 992) {
                // Desktop view - close mobile sidebar
                const sidebar = document.getElementById('sidebar');
                const overlay = document.querySelector('.sidebar-overlay');
                if (sidebar && overlay) {
                    sidebar.classList.remove('active');
                    overlay.classList.remove('active');
                }
            }
        });
        
        // Handle touch events for mobile
        let touchStartX = 0;
        let touchEndX = 0;
        
        document.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });
        
        document.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            this.handleSwipe();
        });
        
        // Add swipe gesture support
        const handleSwipe = () => {
            if (window.innerWidth < 992) {
                const sidebar = document.getElementById('sidebar');
                const swipeThreshold = 50;
                
                // Swipe right to open sidebar
                if (touchEndX - touchStartX > swipeThreshold && touchStartX < 50) {
                    this.openSidebar();
                }
                // Swipe left to close sidebar
                else if (touchStartX - touchEndX > swipeThreshold && sidebar.classList.contains('active')) {
                    this.closeSidebar();
                }
            }
        };
        
        this.handleSwipe = handleSwipe;
    }

    initPWAFeatures() {
        // Add PWA install button functionality
        const installBtn = document.getElementById('install-btn');
        if (installBtn) {
            installBtn.style.display = 'none'; // Hidden by default
        }
        
        // Handle app installed event
        window.addEventListener('appinstalled', (evt) => {
            console.log('App installed successfully');
            // Hide install button if it exists
            if (installBtn) {
                installBtn.style.display = 'none';
            }
        });
    }
}

// Sidebar utility functions for global access
function toggleSidebar() {
    app.toggleSidebar();
}

function closeSidebar() {
    app.closeSidebar();
}

function toggleSidebarCollapse() {
    app.toggleSidebarCollapse();
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.app = new DigitalSkeletonCoinApp();
});

// Mining button functionality
function initMiningButton() {
    const miningBtn = document.getElementById('mining-btn');
    if (miningBtn) {
        miningBtn.addEventListener('click', function() {
            const button = this;
            const originalText = button.innerHTML;
            
            // Disable button and show loading
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Mining...';
            
            // Make mining request
            fetch('/mining/mine', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update balance display
                    updateBalance(data.new_balance);
                    updateXP(data.new_xp);
                    
                    // Show success message
                    showToast('Success', `Mined ${data.coins_earned} coins!`, 'success');
                } else {
                    showToast('Error', data.message || 'Mining failed', 'error');
                }
            })
            .catch(error => {
                console.error('Mining error:', error);
                showToast('Error', 'Network error occurred', 'error');
            })
            .finally(() => {
                // Re-enable button
                button.disabled = false;
                button.innerHTML = originalText;
            });
        });
    }
}

// Utility functions
function updateBalance(newBalance) {
    const balanceElements = document.querySelectorAll('.balance-display');
    balanceElements.forEach(el => {
        el.textContent = parseFloat(newBalance).toFixed(2);
    });
}

function updateXP(newXP) {
    const xpElements = document.querySelectorAll('.xp-display');
    xpElements.forEach(el => {
        el.textContent = newXP;
    });
}

function showToast(title, message, type = 'info') {
    // Create toast notification
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${title}</strong><br>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// Initialize mining button when page loads
document.addEventListener('DOMContentLoaded', initMiningButton);
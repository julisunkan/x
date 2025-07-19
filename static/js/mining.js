// Mining functionality for DigitalSkeletonCoin (DSC) Platform

class MiningManager {
    constructor() {
        this.isMining = false;
        this.cooldownActive = false;
        this.cooldownTimer = null;
        this.animationQueue = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeElements();
        this.startStatsUpdater();
    }

    setupEventListeners() {
        const mineBtn = document.getElementById('mine-btn');
        if (mineBtn) {
            mineBtn.addEventListener('click', () => this.handleMining());
        }

        // Keyboard support for mining (spacebar)
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
                this.handleMining();
            }
        });

        // Touch support for mobile
        if (mineBtn) {
            mineBtn.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.handleMining();
            });
        }
    }

    initializeElements() {
        this.elements = {
            mineBtn: document.getElementById('mine-btn'),
            balanceEl: document.getElementById('user-balance'),
            levelEl: document.getElementById('user-level'),
            xpEl: document.getElementById('user-xp'),
            xpProgressEl: document.getElementById('xp-progress'),
            currentXpEl: document.getElementById('current-xp'),
            nextLevelXpEl: document.getElementById('next-level-xp'),
            miningResult: document.getElementById('mining-result'),
            earnedCoins: document.getElementById('earned-coins'),
            earnedXp: document.getElementById('earned-xp'),
            cooldownDisplay: document.getElementById('cooldown-display'),
            cooldownTimer: document.getElementById('cooldown-timer'),
            floatingCoins: document.getElementById('floating-coins')
        };
    }

    async handleMining() {
        if (this.isMining || this.cooldownActive) {
            return;
        }

        this.isMining = true;
        this.startMiningAnimation();

        try {
            const response = await fetch('/mining/mine', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': window.csrfToken
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.handleMiningSuccess(data);
            } else {
                this.handleMiningError(data.error || 'Mining failed');
            }
        } catch (error) {
            console.error('Mining error:', error);
            this.handleMiningError('Network error occurred');
        } finally {
            this.isMining = false;
            this.stopMiningAnimation();
        }
    }

    handleMiningSuccess(data) {
        // Update UI elements
        this.updateBalance(data.new_balance);
        this.updateXP(data.new_xp, data.new_level);
        this.updateXPProgress(data.xp_progress);

        // Show results
        this.showMiningResult(data.coins_earned, data.xp_earned);

        // Create floating coin animations
        this.createFloatingCoins(data.coins_earned);

        // Check for level up
        if (data.new_level > this.getCurrentLevel()) {
            this.showLevelUpNotification(data.new_level);
        }

        // Start cooldown (1 second)
        this.startCooldown(1000);

        // Update stats in navigation
        this.updateNavStats(data.new_balance, data.new_level, data.new_xp);
    }

    handleMiningError(error) {
        console.error('Mining error:', error);
        
        if (error.includes('cooldown')) {
            this.showNotification('Mining cooldown active. Please wait a moment.', 'warning');
        } else {
            this.showNotification(error, 'error');
        }
    }

    startMiningAnimation() {
        if (this.elements.mineBtn) {
            this.elements.mineBtn.classList.add('mining-active');
            this.elements.mineBtn.disabled = true;
            
            // Add pulsing animation
            this.elements.mineBtn.style.animation = 'miningPulse 0.3s ease';
        }
    }

    stopMiningAnimation() {
        if (this.elements.mineBtn) {
            this.elements.mineBtn.classList.remove('mining-active');
            
            setTimeout(() => {
                if (!this.cooldownActive) {
                    this.elements.mineBtn.disabled = false;
                }
                this.elements.mineBtn.style.animation = '';
            }, 300);
        }
    }

    updateBalance(newBalance) {
        if (this.elements.balanceEl) {
            this.animateNumberChange(this.elements.balanceEl, newBalance, 4);
        }
    }

    updateXP(newXP, newLevel) {
        if (this.elements.xpEl) {
            this.animateNumberChange(this.elements.xpEl, newXP, 0);
        }
        
        if (this.elements.levelEl && newLevel) {
            this.animateNumberChange(this.elements.levelEl, newLevel, 0);
        }
    }

    updateXPProgress(progressPercentage) {
        if (this.elements.xpProgressEl) {
            this.elements.xpProgressEl.style.width = `${progressPercentage}%`;
        }
    }

    getCurrentLevel() {
        return this.elements.levelEl ? parseInt(this.elements.levelEl.textContent) : 1;
    }

    showMiningResult(coinsEarned, xpEarned) {
        if (this.elements.miningResult) {
            if (this.elements.earnedCoins) {
                this.elements.earnedCoins.textContent = parseFloat(coinsEarned).toFixed(4);
            }
            if (this.elements.earnedXp) {
                this.elements.earnedXp.textContent = xpEarned;
            }
            
            this.elements.miningResult.style.display = 'block';
            this.elements.miningResult.classList.add('show');
            
            // Auto-hide after 3 seconds
            setTimeout(() => {
                if (this.elements.miningResult) {
                    this.elements.miningResult.style.display = 'none';
                    this.elements.miningResult.classList.remove('show');
                }
            }, 3000);
        }
    }

    createFloatingCoins(amount) {
        if (!this.elements.floatingCoins) return;

        const coinCount = Math.min(Math.ceil(amount / 10), 5); // Max 5 coins
        
        for (let i = 0; i < coinCount; i++) {
            setTimeout(() => {
                this.createSingleFloatingCoin();
            }, i * 100);
        }
    }

    createSingleFloatingCoin() {
        const coin = document.createElement('div');
        coin.className = 'floating-coin';
        coin.innerHTML = '<i class="fas fa-coins"></i>';
        
        // Random starting position around the mine button
        const mineBtn = this.elements.mineBtn;
        if (mineBtn) {
            const btnRect = mineBtn.getBoundingClientRect();
            const containerRect = this.elements.floatingCoins.getBoundingClientRect();
            
            const startX = (btnRect.left - containerRect.left) + (btnRect.width / 2) + (Math.random() - 0.5) * 100;
            const startY = (btnRect.top - containerRect.top) + (btnRect.height / 2);
            
            coin.style.left = `${startX}px`;
            coin.style.top = `${startY}px`;
        }
        
        this.elements.floatingCoins.appendChild(coin);
        
        // Remove coin after animation
        setTimeout(() => {
            if (coin.parentNode) {
                coin.parentNode.removeChild(coin);
            }
        }, 2000);
    }

    showLevelUpNotification(newLevel) {
        const notification = document.createElement('div');
        notification.className = 'level-up-notification';
        notification.innerHTML = `
            <i class="fas fa-star me-2"></i>
            <div>
                <div style="font-size: 1.8rem;">LEVEL UP!</div>
                <div style="font-size: 1.2rem;">You reached level ${newLevel}!</div>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Add sound effect if available
        this.playLevelUpSound();
        
        // Remove notification after animation
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    playLevelUpSound() {
        // Simple beep sound using Web Audio API
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1);
            oscillator.frequency.setValueAtTime(1200, audioContext.currentTime + 0.2);
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (error) {
            // Ignore audio errors
        }
    }

    startCooldown(duration) {
        this.cooldownActive = true;
        
        if (this.elements.mineBtn) {
            this.elements.mineBtn.disabled = true;
        }
        
        if (this.elements.cooldownDisplay) {
            this.elements.cooldownDisplay.style.display = 'block';
        }
        
        let remaining = Math.ceil(duration / 1000);
        
        const updateTimer = () => {
            if (this.elements.cooldownTimer) {
                this.elements.cooldownTimer.textContent = remaining;
            }
            
            remaining--;
            
            if (remaining >= 0) {
                this.cooldownTimer = setTimeout(updateTimer, 1000);
            } else {
                this.endCooldown();
            }
        };
        
        updateTimer();
    }

    endCooldown() {
        this.cooldownActive = false;
        
        if (this.cooldownTimer) {
            clearTimeout(this.cooldownTimer);
            this.cooldownTimer = null;
        }
        
        if (this.elements.cooldownDisplay) {
            this.elements.cooldownDisplay.style.display = 'none';
        }
        
        if (this.elements.mineBtn && !this.isMining) {
            this.elements.mineBtn.disabled = false;
        }
    }

    animateNumberChange(element, newValue, decimals = 0) {
        const currentValue = parseFloat(element.textContent.replace(/,/g, '')) || 0;
        const difference = newValue - currentValue;
        const steps = 20;
        const stepValue = difference / steps;
        const stepDuration = 50;
        
        let currentStep = 0;
        
        const updateValue = () => {
            currentStep++;
            const value = currentValue + (stepValue * currentStep);
            
            if (decimals > 0) {
                element.textContent = value.toFixed(decimals);
            } else {
                element.textContent = Math.round(value).toLocaleString();
            }
            
            if (currentStep < steps) {
                setTimeout(updateValue, stepDuration);
            } else {
                // Ensure final value is exact
                if (decimals > 0) {
                    element.textContent = newValue.toFixed(decimals);
                } else {
                    element.textContent = Math.round(newValue).toLocaleString();
                }
            }
        };
        
        updateValue();
    }

    updateNavStats(balance, level, xp) {
        // Update stats in navigation bar
        const navBalance = document.querySelector('.navbar .badge:has(.fa-coins)');
        const navLevel = document.querySelector('.navbar .badge:has(.fa-star)');
        const navXP = document.querySelector('.navbar .badge:has(.fa-bolt)');
        
        if (navBalance) {
            navBalance.innerHTML = `<i class="fas fa-coins me-1"></i>${balance.toFixed(4)}`;
        }
        
        if (navLevel) {
            navLevel.innerHTML = `<i class="fas fa-star me-1"></i>Lvl ${level}`;
        }
        
        if (navXP) {
            navXP.innerHTML = `<i class="fas fa-bolt me-1"></i>${xp} XP`;
        }
    }

    showNotification(message, type = 'info') {
        const alertClass = type === 'error' ? 'alert-danger' : `alert-${type}`;
        
        const notification = document.createElement('div');
        notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
        `;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    startStatsUpdater() {
        // Update mining stats every 30 seconds
        setInterval(() => {
            this.updateMiningStats();
        }, 30000);
    }

    async updateMiningStats() {
        try {
            const response = await fetch('/mining/stats', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Update any stats that might have changed
                if (data.balance !== undefined) {
                    this.updateBalance(data.balance);
                }
                
                if (data.xp !== undefined && data.level !== undefined) {
                    this.updateXP(data.xp, data.level);
                }
                
                if (data.xp_progress !== undefined) {
                    this.updateXPProgress(data.xp_progress);
                }
            }
        } catch (error) {
            // Silently fail - stats will update on next mining action
        }
    }

    // Daily mission claim functionality
    async claimMissionReward(missionId) {
        try {
            const response = await fetch(`/mining/claim-mission/${missionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.showNotification('Mission reward claimed!', 'success');
                
                // Refresh the page to update mission status
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                this.showNotification(data.error || 'Failed to claim reward', 'error');
            }
        } catch (error) {
            this.showNotification('Network error occurred', 'error');
        }
    }
}

// Auto-start mining functionality when page loads
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('mine-btn')) {
        window.miningManager = new MiningManager();
    }
});

// Global function for mission reward claiming
function claimMissionReward(missionId) {
    if (window.miningManager) {
        window.miningManager.claimMissionReward(missionId);
    }
}

// Keyboard shortcut help
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        alert('Mining Controls:\n\nSpacebar - Mine DigitalSkeletonCoin (DSC)s\nCtrl+/ - Show this help');
    }
});

// Performance optimization: requestAnimationFrame for smooth animations
function smoothAnimation(callback) {
    requestAnimationFrame(callback);
}

// Export for testing/modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MiningManager;
}

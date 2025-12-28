// Telegram WebApp Optimization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Telegram Web App
    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        
        // Enable expansion
        tg.expand();
        
        // Set header color
        tg.setHeaderColor('#0b0e11');
        tg.setBackgroundColor('#0b0e11');
        
        // Enable viewport fit
        if (tg.isVersionAtLeast && tg.isVersionAtLeast(6.1)) {
            tg.setBottomBarColor('#0b0e11');
        }
        
        // Ready signal
        tg.ready();
        
        // Store viewport info
        window.tgViewport = {
            width: tg.viewportStableHeight,
            height: tg.viewportHeight,
            isExpanded: tg.isExpanded
        };
        
        // Handle viewport changes
        tg.onEvent('viewportChanged', () => {
            window.tgViewport = {
                width: tg.viewportStableHeight,
                height: tg.viewportHeight,
                isExpanded: tg.isExpanded
            };
            adjustLayoutForViewport();
        });
    }
    
    // Adjust layout based on viewport
    adjustLayoutForViewport();
    
    // Handle window resize
    window.addEventListener('resize', adjustLayoutForViewport);
    window.addEventListener('orientationchange', adjustLayoutForViewport);
});

function adjustLayoutForViewport() {
    const mainContent = document.querySelector('.main-content');
    if (mainContent && window.tgViewport) {
        const safeArea = getComputedStyle(document.documentElement);
        const topInset = parseInt(safeArea.getPropertyValue('--safe-area-inset-top')) || 0;
        const bottomInset = parseInt(safeArea.getPropertyValue('--safe-area-inset-bottom')) || 0;
        
        const availableHeight = window.tgViewport.height - topInset - bottomInset;
        mainContent.style.minHeight = availableHeight + 'px';
    }
}

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('mobile-active');
            if (overlay) {
                overlay.classList.toggle('active');
            }
        });
        
        if (overlay) {
            overlay.addEventListener('click', function() {
                sidebar.classList.remove('mobile-active');
                overlay.classList.remove('active');
            });
        }
    }
});

// Disable zoom on double tap for Telegram WebApp
document.addEventListener('touchstart', function(e) {
    if (e.touches.length > 1) {
        e.preventDefault();
    }
}, { passive: false });

let lastTouchEnd = 0;
document.addEventListener('touchend', function(e) {
    const now = Date.now();
    if (now - lastTouchEnd <= 300) {
        e.preventDefault();
    }
    lastTouchEnd = now;
}, false);

// Optimize for slow networks
if ('connection' in navigator) {
    const conn = navigator.connection;
    if (conn.saveData || conn.effectiveType === '4g' || conn.effectiveType === '3g') {
        document.documentElement.setAttribute('data-low-bandwidth', 'true');
    }
}

// Haptic feedback for buttons (if supported)
document.addEventListener('click', function(e) {
    const button = e.target.closest('button, a.button, [role="button"]');
    if (button && window.Telegram && window.Telegram.WebApp) {
        try {
            window.Telegram.WebApp.HapticFeedback?.impactOccurred?.('light');
        } catch (err) {
            // Haptic feedback not available
        }
    }
});

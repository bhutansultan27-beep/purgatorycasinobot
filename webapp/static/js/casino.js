let tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

let userData = null;

document.addEventListener('DOMContentLoaded', function() {
    initTelegram();
    loadUserData();
    initSidebar();
    initCategoryTabs();
    initSearch();
});

function initTelegram() {
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const user = tg.initDataUnsafe.user;
        document.getElementById('user-name').textContent = user.first_name + (user.last_name ? ' ' + user.last_name : '');
        
        const initial = user.first_name.charAt(0).toUpperCase();
        document.getElementById('avatar-initial').textContent = initial;
        
        if (user.photo_url) {
            setAvatarPhoto(user.photo_url);
        }
    }
    
    tg.setHeaderColor('#0d0d0f');
    tg.setBackgroundColor('#0d0d0f');
}

function setAvatarPhoto(url) {
    const headerAvatar = document.getElementById('user-avatar');
    const largeAvatar = document.getElementById('user-avatar-large');
    
    if (headerAvatar) {
        headerAvatar.style.backgroundImage = `url(${url})`;
        headerAvatar.style.backgroundSize = 'cover';
        headerAvatar.style.backgroundPosition = 'center';
        const initial = headerAvatar.querySelector('#avatar-initial');
        if (initial) initial.style.display = 'none';
    }
    
    if (largeAvatar) {
        largeAvatar.style.backgroundImage = `url(${url})`;
        largeAvatar.style.backgroundSize = 'cover';
        largeAvatar.style.backgroundPosition = 'center';
        largeAvatar.textContent = '';
    }
}

function loadUserData() {
    const initData = tg.initData || '';
    
    fetch('/api/user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ initData: initData })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            userData = data.user;
            if (data.bot_username) {
                setBotUsername(data.bot_username);
            }
            updateUI();
        } else {
            showDemoData();
        }
    })
    .catch(error => {
        console.log('Using demo data');
        showDemoData();
    });
}

function updateUI() {
    if (userData) {
        document.getElementById('balance').textContent = '$' + formatNumber(userData.balance);
        document.getElementById('user-level').innerHTML = `<span class="level-badge">${userData.level_emoji} ${userData.level_name}</span>`;
        document.getElementById('total-wagered').textContent = '$' + formatNumber(userData.total_wagered);
        document.getElementById('total-won').textContent = '$' + formatNumber(userData.total_won);
        document.getElementById('games-played').textContent = userData.games_played || 0;
        document.getElementById('win-rate').textContent = (userData.win_rate || 0) + '%';
        
        if (userData.photo_url) {
            setAvatarPhoto(userData.photo_url);
        }
        
        if (userData.is_admin) {
            const adminNav = document.getElementById('admin-nav');
            if (adminNav) {
                adminNav.style.display = 'block';
            }
        }
    }
}

function showDemoData() {
    document.getElementById('balance').textContent = '$0.00';
    document.getElementById('user-name').textContent = 'Demo Player';
    document.getElementById('total-wagered').textContent = '$0';
    document.getElementById('total-won').textContent = '$0';
    document.getElementById('games-played').textContent = '0';
    document.getElementById('win-rate').textContent = '0%';
}

function formatNumber(num) {
    if (num === undefined || num === null) return '0.00';
    return parseFloat(num).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

let botUsername = null;

function setBotUsername(username) {
    botUsername = username;
    console.log('Bot username set to:', username);
}

function openBotCommand(command) {
    const cleanCommand = command.startsWith('/') ? command.substring(1) : command;
    
    tg.showConfirm(`Close and use /${cleanCommand} in the bot chat?`, function(confirmed) {
        if (confirmed) {
            tg.close();
        }
    });
}

function initSidebar() {
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('open');
        });
    }
    
    if (overlay) {
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('open');
            overlay.classList.remove('open');
        });
    }
}

function initCategoryTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    const sections = document.querySelectorAll('.games-section');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            const category = this.dataset.tab;
            const gamesSection = document.getElementById('games-section');
            const tableSection = document.getElementById('table-section');
            const slotsSection = document.getElementById('slots-section');
            
            if (category === 'all') {
                if (gamesSection) gamesSection.style.display = 'block';
                if (tableSection) tableSection.style.display = 'block';
                if (slotsSection) slotsSection.style.display = 'block';
            } else if (category === 'originals') {
                if (gamesSection) gamesSection.style.display = 'block';
                if (tableSection) tableSection.style.display = 'none';
                if (slotsSection) slotsSection.style.display = 'none';
            } else if (category === 'table') {
                if (gamesSection) gamesSection.style.display = 'none';
                if (tableSection) tableSection.style.display = 'block';
                if (slotsSection) slotsSection.style.display = 'none';
            }
        });
    });
}

function initSearch() {
    const searchInput = document.getElementById('game-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const gameCards = document.querySelectorAll('.game-card-new');
            
            gameCards.forEach(card => {
                const gameName = card.querySelector('h3').textContent.toLowerCase();
                if (gameName.includes(query)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = query ? 'none' : 'block';
                }
            });
        });
    }
}

function scrollGames(section, direction) {
    const scrollContainer = document.getElementById(section + '-scroll');
    if (scrollContainer) {
        const scrollAmount = 200;
        scrollContainer.scrollBy({
            left: scrollAmount * direction,
            behavior: 'smooth'
        });
    }
}

function showDeposit() {
    openBotCommand('/deposit');
}

function showWithdraw() {
    openBotCommand('/withdraw');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

function selectCrypto(crypto) {
    openBotCommand(`/deposit_${crypto.toLowerCase()}`);
}

function showProfile() {
    window.location.href = '/profile';
}

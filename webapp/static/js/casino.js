let tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

let userData = null;

document.addEventListener('DOMContentLoaded', function() {
    initTelegram();
    loadUserData();
});

function initTelegram() {
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const user = tg.initDataUnsafe.user;
        document.getElementById('user-name').textContent = user.first_name + (user.last_name ? ' ' + user.last_name : '');
        
        if (user.photo_url) {
            document.getElementById('user-avatar').style.backgroundImage = `url(${user.photo_url})`;
            document.getElementById('user-avatar').style.backgroundSize = 'cover';
            document.getElementById('user-avatar').textContent = '';
        } else {
            document.getElementById('user-avatar').textContent = user.first_name.charAt(0).toUpperCase();
        }
    }
    
    tg.setHeaderColor('#0a0a0a');
    tg.setBackgroundColor('#0a0a0a');
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
        
        if (userData.is_admin) {
            const adminSection = document.getElementById('admin-section');
            if (adminSection) {
                adminSection.style.display = 'block';
            }
        }
    }
}

function showDemoData() {
    document.getElementById('balance').textContent = '$1,000.00';
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
    
    // Show user the command they need to use, then close the mini app
    tg.showConfirm(`Close and use /${cleanCommand} in the bot chat?`, function(confirmed) {
        if (confirmed) {
            tg.close();
        }
    });
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
    openBotCommand('/profile');
}

function showLeaderboard() {
    openBotCommand('/leaderboard');
}

function showHistory() {
    openBotCommand('/history');
}

function showSupport() {
    openBotCommand('/support');
}

document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

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

function showDeposit() {
    document.getElementById('deposit-modal').classList.add('active');
}

function showWithdraw() {
    document.getElementById('withdraw-modal').classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

function selectCrypto(crypto) {
    tg.showAlert(`To deposit ${crypto}, use /deposit ${crypto.toLowerCase()} in the bot chat.`);
    closeModal('deposit-modal');
}

function showProfile() {
    tg.showAlert('Use /profile in the bot to view your full profile.');
}

function showLeaderboard() {
    tg.showAlert('Use /leaderboard in the bot to view the leaderboard.');
}

function showHistory() {
    tg.showAlert('Use /history in the bot to view your game history.');
}

function showSupport() {
    tg.showAlert('Contact @YourSupportUsername for support.');
}

document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

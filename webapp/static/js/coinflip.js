let balance = 0;
let currentBet = 0;
let selectedChoice = null;
let isFlipping = false;

document.addEventListener('DOMContentLoaded', function() {
    initTelegram();
    setupEventListeners();
});

function initTelegram() {
    if (window.Telegram && window.Telegram.WebApp) {
        Telegram.WebApp.ready();
        Telegram.WebApp.expand();
        loadUserData();
    } else {
        balance = 100;
        updateBalanceDisplay();
    }
}

function loadUserData() {
    fetch('/api/user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initData: Telegram.WebApp.initData })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success && data.user) {
            balance = data.user.balance || 0;
            updateBalanceDisplay();
        }
    })
    .catch(err => console.error('Error loading user:', err));
}

function setupEventListeners() {
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const value = parseInt(chip.dataset.value);
            if (value <= balance) {
                currentBet += value;
                updateBetDisplay();
                document.querySelectorAll('.chip').forEach(c => c.classList.remove('selected'));
                chip.classList.add('selected');
            } else {
                showMessage('Insufficient balance');
            }
        });
    });

    document.getElementById('btn-heads').addEventListener('click', () => selectChoice('heads'));
    document.getElementById('btn-tails').addEventListener('click', () => selectChoice('tails'));
    document.getElementById('btn-clear').addEventListener('click', clearBet);
    document.getElementById('btn-flip').addEventListener('click', flip);
    document.getElementById('btn-new-game').addEventListener('click', newGame);
}

function selectChoice(choice) {
    selectedChoice = choice;
    document.querySelectorAll('.choice-btn').forEach(btn => btn.classList.remove('selected'));
    document.querySelector(`.choice-btn.${choice}`).classList.add('selected');
    updateFlipButton();
}

function updateBalanceDisplay() {
    document.getElementById('balance').textContent = `$${balance.toFixed(2)}`;
}

function updateBetDisplay() {
    document.getElementById('bet-display').textContent = `$${currentBet}`;
    updateFlipButton();
}

function updateFlipButton() {
    const btn = document.getElementById('btn-flip');
    btn.disabled = currentBet <= 0 || !selectedChoice || isFlipping;
}

function clearBet() {
    currentBet = 0;
    selectedChoice = null;
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('selected'));
    document.querySelectorAll('.choice-btn').forEach(b => b.classList.remove('selected'));
    updateBetDisplay();
}

function flip() {
    if (currentBet <= 0 || !selectedChoice || isFlipping) return;
    if (currentBet > balance) {
        showMessage('Insufficient balance');
        return;
    }

    isFlipping = true;
    updateFlipButton();

    const coin = document.getElementById('coin');
    coin.classList.add('flipping');

    fetch('/api/coinflip/play', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            initData: window.Telegram?.WebApp?.initData || '',
            bet: currentBet,
            choice: selectedChoice
        })
    })
    .then(res => res.json())
    .then(data => {
        setTimeout(() => {
            coin.classList.remove('flipping');
            
            if (data.success) {
                coin.classList.remove('heads', 'tails');
                coin.classList.add(data.result);

                balance = data.newBalance;
                updateBalanceDisplay();

                showResult(data.result, data.win, data.payout);
            } else {
                showMessage(data.error || 'Error playing game');
            }
            isFlipping = false;
        }, 1500);
    })
    .catch(err => {
        coin.classList.remove('flipping');
        isFlipping = false;
        showMessage('Network error');
        console.error(err);
    });
}

function showResult(result, isWin, payout) {
    const overlay = document.getElementById('result-overlay');
    const icon = document.getElementById('result-icon');
    const title = document.getElementById('result-title');
    const amount = document.getElementById('result-amount');

    icon.textContent = result === 'heads' ? '👑' : '🦅';

    if (isWin) {
        title.textContent = 'You Win!';
        title.className = 'result-title win';
        amount.textContent = `+$${payout.toFixed(2)}`;
        amount.className = 'result-amount win';
    } else {
        title.textContent = 'You Lose';
        title.className = 'result-title lose';
        amount.textContent = `-$${currentBet.toFixed(2)}`;
        amount.className = 'result-amount lose';
    }

    overlay.classList.add('show');
}

function newGame() {
    document.getElementById('result-overlay').classList.remove('show');
    clearBet();
}

function showMessage(msg) {
    const toast = document.getElementById('message-toast');
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2000);
}

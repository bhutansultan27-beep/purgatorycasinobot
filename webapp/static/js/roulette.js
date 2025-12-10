let balance = 0;
let currentBet = 0;
let selectedBetType = null;
let isSpinning = false;
let lastResults = [];

const RED_NUMBERS = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];
const BLACK_NUMBERS = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35];
const GREEN_NUMBERS = [0];

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

    document.querySelectorAll('.bet-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.bet-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            selectedBetType = btn.dataset.bet;
            updateSpinButton();
        });
    });

    document.getElementById('btn-clear').addEventListener('click', clearBet);
    document.getElementById('btn-spin').addEventListener('click', spin);
    document.getElementById('btn-new-game').addEventListener('click', newGame);
}

function updateBalanceDisplay() {
    document.getElementById('balance').textContent = `$${balance.toFixed(2)}`;
}

function updateBetDisplay() {
    document.getElementById('bet-display').textContent = `$${currentBet}`;
    updateSpinButton();
}

function updateSpinButton() {
    const btn = document.getElementById('btn-spin');
    btn.disabled = currentBet <= 0 || !selectedBetType || isSpinning;
}

function clearBet() {
    currentBet = 0;
    selectedBetType = null;
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('selected'));
    document.querySelectorAll('.bet-btn').forEach(b => b.classList.remove('selected'));
    updateBetDisplay();
}

function spin() {
    if (currentBet <= 0 || !selectedBetType || isSpinning) return;
    if (currentBet > balance) {
        showMessage('Insufficient balance');
        return;
    }

    isSpinning = true;
    updateSpinButton();

    const wheel = document.getElementById('roulette-wheel');
    wheel.classList.add('spinning');

    fetch('/api/roulette/play', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            initData: window.Telegram?.WebApp?.initData || '',
            bet: currentBet,
            betType: selectedBetType
        })
    })
    .then(res => res.json())
    .then(data => {
        setTimeout(() => {
            wheel.classList.remove('spinning');
            
            if (data.success) {
                const result = data.result;
                document.getElementById('result-number').textContent = result;
                
                balance = data.newBalance;
                updateBalanceDisplay();

                addToHistory(result);
                showResult(result, data.win, data.payout, data.color);
            } else {
                showMessage(data.error || 'Error playing game');
            }
            isSpinning = false;
        }, 2000);
    })
    .catch(err => {
        wheel.classList.remove('spinning');
        isSpinning = false;
        showMessage('Network error');
        console.error(err);
    });
}

function addToHistory(result) {
    let color = 'green';
    if (RED_NUMBERS.includes(result)) color = 'red';
    else if (BLACK_NUMBERS.includes(result)) color = 'black';

    lastResults.unshift({ number: result, color: color });
    if (lastResults.length > 8) lastResults.pop();

    const row = document.getElementById('results-row');
    row.innerHTML = '';
    lastResults.forEach(r => {
        const dot = document.createElement('div');
        dot.className = `result-dot ${r.color}`;
        dot.textContent = r.number;
        row.appendChild(dot);
    });
}

function showResult(number, isWin, payout, color) {
    const overlay = document.getElementById('result-overlay');
    const numberBig = document.getElementById('result-number-big');
    const title = document.getElementById('result-title');
    const amount = document.getElementById('result-amount');

    numberBig.textContent = number;
    numberBig.style.color = color === 'red' ? '#c0392b' : color === 'green' ? '#27ae60' : '#fff';

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

let tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const symbols = ['🍒', '🍋', '🍊', '🍇', '⭐', '💎', '7️⃣'];
const payouts = {
    '🍒🍒🍒': 5,
    '🍋🍋🍋': 10,
    '🍊🍊🍊': 15,
    '🍇🍇🍇': 20,
    '⭐⭐⭐': 50,
    '💎💎💎': 100,
    '7️⃣7️⃣7️⃣': 777
};

let balance = 1000;
let currentBet = 10;
let isSpinning = false;

const reel1 = document.getElementById('reel1');
const reel2 = document.getElementById('reel2');
const reel3 = document.getElementById('reel3');
const spinBtn = document.getElementById('spin-btn');
const betDisplay = document.getElementById('bet-display');
const balanceDisplay = document.getElementById('balance');
const winDisplay = document.getElementById('win-display');

document.querySelectorAll('.preset').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.preset').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentBet = parseInt(btn.dataset.value);
        betDisplay.textContent = '$' + currentBet;
    });
});

document.getElementById('bet-decrease').addEventListener('click', () => {
    if (currentBet > 1) {
        currentBet = Math.max(1, currentBet - 5);
        betDisplay.textContent = '$' + currentBet;
        updatePresetButtons();
    }
});

document.getElementById('bet-increase').addEventListener('click', () => {
    if (currentBet < balance) {
        currentBet = Math.min(balance, currentBet + 5);
        betDisplay.textContent = '$' + currentBet;
        updatePresetButtons();
    }
});

function updatePresetButtons() {
    document.querySelectorAll('.preset').forEach(btn => {
        btn.classList.toggle('active', parseInt(btn.dataset.value) === currentBet);
    });
}

spinBtn.addEventListener('click', spin);

function spin() {
    if (isSpinning || currentBet > balance) return;
    
    isSpinning = true;
    balance -= currentBet;
    updateBalance();
    winDisplay.textContent = '';
    winDisplay.classList.remove('win');
    spinBtn.disabled = true;
    
    reel1.classList.add('spinning');
    reel2.classList.add('spinning');
    reel3.classList.add('spinning');
    
    const spinInterval = setInterval(() => {
        reel1.textContent = symbols[Math.floor(Math.random() * symbols.length)];
        reel2.textContent = symbols[Math.floor(Math.random() * symbols.length)];
        reel3.textContent = symbols[Math.floor(Math.random() * symbols.length)];
    }, 100);
    
    setTimeout(() => {
        clearInterval(spinInterval);
        
        const result1 = getRandomSymbol();
        const result2 = getRandomSymbol();
        const result3 = getRandomSymbol();
        
        reel1.classList.remove('spinning');
        reel1.textContent = result1;
        
        setTimeout(() => {
            reel2.classList.remove('spinning');
            reel2.textContent = result2;
            
            setTimeout(() => {
                reel3.classList.remove('spinning');
                reel3.textContent = result3;
                
                checkWin(result1, result2, result3);
                isSpinning = false;
                spinBtn.disabled = false;
            }, 300);
        }, 300);
    }, 1500);
}

function getRandomSymbol() {
    const weights = [30, 25, 20, 15, 7, 2, 1];
    const totalWeight = weights.reduce((a, b) => a + b, 0);
    let random = Math.random() * totalWeight;
    
    for (let i = 0; i < symbols.length; i++) {
        random -= weights[i];
        if (random <= 0) {
            return symbols[i];
        }
    }
    return symbols[0];
}

function checkWin(s1, s2, s3) {
    const combo = s1 + s2 + s3;
    
    if (payouts[combo]) {
        const winAmount = currentBet * payouts[combo];
        balance += winAmount;
        updateBalance();
        winDisplay.textContent = `WIN! +$${winAmount}`;
        winDisplay.classList.add('win');
        
        if (tg.HapticFeedback) {
            tg.HapticFeedback.notificationOccurred('success');
        }
    } else if (s1 === s2 || s2 === s3) {
        const winAmount = Math.floor(currentBet * 0.5);
        if (winAmount > 0) {
            balance += winAmount;
            updateBalance();
            winDisplay.textContent = `Small win! +$${winAmount}`;
        }
    }
}

function updateBalance() {
    balanceDisplay.textContent = '$' + balance.toLocaleString('en-US', { minimumFractionDigits: 2 });
}

let tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

let balance = 1000;
let currentBet = 10;
let minesCount = 3;
let gameActive = false;
let revealedCount = 0;
let minePositions = [];
let currentMultiplier = 1.00;

const grid = document.getElementById('mines-grid');
const balanceDisplay = document.getElementById('balance');
const multiplierDisplay = document.getElementById('multiplier');
const potentialWinDisplay = document.getElementById('potential-win');
const startBtn = document.getElementById('start-btn');
const cashoutBtn = document.getElementById('cashout-btn');

function initGrid() {
    grid.innerHTML = '';
    for (let i = 0; i < 25; i++) {
        const tile = document.createElement('div');
        tile.className = 'mine-tile';
        tile.dataset.index = i;
        tile.addEventListener('click', () => revealTile(i));
        grid.appendChild(tile);
    }
}

initGrid();

function adjustBet(amount) {
    if (gameActive) return;
    const input = document.getElementById('bet-amount');
    let newValue = Math.max(1, Math.min(balance, parseInt(input.value) + amount));
    input.value = newValue;
    currentBet = newValue;
}

function adjustMines(amount) {
    if (gameActive) return;
    const input = document.getElementById('mines-count');
    let newValue = Math.max(1, Math.min(24, parseInt(input.value) + amount));
    input.value = newValue;
    minesCount = newValue;
}

function startGame() {
    currentBet = parseInt(document.getElementById('bet-amount').value);
    minesCount = parseInt(document.getElementById('mines-count').value);
    
    if (currentBet > balance) {
        alert('Insufficient balance!');
        return;
    }
    
    balance -= currentBet;
    updateBalance();
    
    gameActive = true;
    revealedCount = 0;
    currentMultiplier = 1.00;
    
    minePositions = [];
    while (minePositions.length < minesCount) {
        const pos = Math.floor(Math.random() * 25);
        if (!minePositions.includes(pos)) {
            minePositions.push(pos);
        }
    }
    
    initGrid();
    updateMultiplier();
    
    startBtn.style.display = 'none';
    cashoutBtn.style.display = 'block';
    
    document.querySelectorAll('.bet-adjust, .controls-section input').forEach(el => {
        el.disabled = true;
    });
}

function revealTile(index) {
    if (!gameActive) return;
    
    const tile = grid.children[index];
    if (tile.classList.contains('revealed')) return;
    
    tile.classList.add('revealed');
    
    if (minePositions.includes(index)) {
        tile.classList.add('bomb');
        tile.textContent = '💣';
        gameOver();
    } else {
        tile.classList.add('gem');
        tile.textContent = '💎';
        revealedCount++;
        updateMultiplier();
        
        if (tg.HapticFeedback) {
            tg.HapticFeedback.impactOccurred('light');
        }
        
        if (revealedCount === 25 - minesCount) {
            cashout();
        }
    }
}

function updateMultiplier() {
    const safeSpots = 25 - minesCount;
    const remaining = safeSpots - revealedCount;
    
    if (revealedCount === 0) {
        currentMultiplier = 1.00;
    } else {
        let multiplier = 1;
        for (let i = 0; i < revealedCount; i++) {
            multiplier *= (25 - i) / (safeSpots - i);
        }
        currentMultiplier = Math.max(1.01, multiplier * 0.97);
    }
    
    multiplierDisplay.textContent = currentMultiplier.toFixed(2) + 'x';
    potentialWinDisplay.textContent = '$' + (currentBet * currentMultiplier).toFixed(2);
}

function cashout() {
    if (!gameActive || revealedCount === 0) return;
    
    const winAmount = currentBet * currentMultiplier;
    balance += winAmount;
    updateBalance();
    
    revealAllMines();
    endGame();
    
    if (tg.HapticFeedback) {
        tg.HapticFeedback.notificationOccurred('success');
    }
    
    alert(`You cashed out $${winAmount.toFixed(2)}!`);
}

function gameOver() {
    gameActive = false;
    revealAllMines();
    endGame();
    
    if (tg.HapticFeedback) {
        tg.HapticFeedback.notificationOccurred('error');
    }
}

function revealAllMines() {
    minePositions.forEach(pos => {
        const tile = grid.children[pos];
        if (!tile.classList.contains('revealed')) {
            tile.classList.add('revealed', 'bomb');
            tile.textContent = '💣';
        }
    });
}

function endGame() {
    gameActive = false;
    startBtn.style.display = 'block';
    cashoutBtn.style.display = 'none';
    
    document.querySelectorAll('.bet-adjust, .controls-section input').forEach(el => {
        el.disabled = false;
    });
    
    document.querySelectorAll('.mine-tile').forEach(tile => {
        tile.classList.add('disabled');
    });
}

function updateBalance() {
    balanceDisplay.textContent = '$' + balance.toLocaleString('en-US', { minimumFractionDigits: 2 });
}

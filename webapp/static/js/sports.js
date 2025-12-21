let tg = window.Telegram.WebApp;
let sportsUserData = null;

document.addEventListener('DOMContentLoaded', function() {
    initTelegram();
    loadSportsUserData();
    initSidebar();
    loadSportsOdds();
    
    const leagueFilter = document.getElementById('sports-league');
    if (leagueFilter) {
        leagueFilter.addEventListener('change', loadSportsOdds);
    }
});

function initTelegram() {
    tg.setHeaderColor('#0d0d0f');
    tg.setBackgroundColor('#0d0d0f');
}

function loadSportsUserData() {
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
            sportsUserData = data.user;
            updateSportsUI();
        }
    })
    .catch(error => console.error('Error loading user data:', error));
}

function updateSportsUI() {
    if (sportsUserData) {
        const balanceEl = document.getElementById('balance');
        if (balanceEl) {
            balanceEl.textContent = '$' + formatNumber(sportsUserData.balance);
        }
    }
}

function formatNumber(num) {
    if (num === undefined || num === null) return '0.00';
    return parseFloat(num).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function loadSportsOdds() {
    const container = document.getElementById('sports-container');
    const league = document.getElementById('sports-league').value;
    
    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading live odds...</p></div>';
    
    fetch('/api/sports/odds', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ league: league })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.odds && data.odds.length > 0) {
            displayOdds(data.odds);
        } else {
            container.innerHTML = '<div class="error-message">No live odds available at the moment. Please try again later.</div>';
        }
    })
    .catch(error => {
        console.error('Error loading odds:', error);
        container.innerHTML = '<div class="error-message">Failed to load odds. Please try again.</div>';
    });
}

function displayOdds(odds) {
    const container = document.getElementById('sports-container');
    container.innerHTML = '';
    
    odds.forEach(event => {
        const eventEl = document.createElement('div');
        eventEl.className = 'sports-event';
        
        const isLive = event.status === 'live';
        const eventTime = new Date(event.commence_time).toLocaleString();
        
        eventEl.innerHTML = `
            <div class="event-header">
                <div style="flex: 1;">
                    <div class="event-title">${event.home_team} vs ${event.away_team}</div>
                </div>
                <div style="display: flex; gap: 8px;">
                    ${isLive ? '<div class="event-live"><span class="live-dot"></span>LIVE</div>' : ''}
                    <div class="event-time">${new Date(event.commence_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                </div>
            </div>
            <div class="odds-row">
                <div class="odds-card" onclick="openSportsBetModal('${event.id}', '${event.home_team}', '${event.home_team}', ${event.home_odds})">
                    <div class="team-name">${event.home_team}</div>
                    <div class="odds-value">${event.home_odds > 0 ? '+' : ''}${event.home_odds}</div>
                </div>
                <div class="odds-card" onclick="openSportsBetModal('${event.id}', '${event.away_team}', '${event.away_team}', ${event.away_odds})">
                    <div class="team-name">${event.away_team}</div>
                    <div class="odds-value">${event.away_odds > 0 ? '+' : ''}${event.away_odds}</div>
                </div>
            </div>
        `;
        
        container.appendChild(eventEl);
    });
}

function openSportsBetModal(eventId, homeTeam, selectedTeam, odds) {
    const content = document.getElementById('sports-bet-modal-content');
    
    content.innerHTML = `
        <div>
            <div class="bet-input-group">
                <label class="bet-label">Betting on: <strong>${selectedTeam}</strong></label>
                <label class="bet-label">Odds: <strong>${odds > 0 ? '+' : ''}${odds}</strong></label>
            </div>
            
            <div class="bet-input-group">
                <label class="bet-label">Enter Bet Amount ($)</label>
                <input type="number" id="sports-bet-amount" class="bet-input" placeholder="Enter amount" min="0.10" step="0.10">
            </div>
            
            <div class="bet-summary">
                <div class="summary-row">
                    <span>Potential Payout:</span>
                    <span>$<span id="sports-potential-payout">0.00</span></span>
                </div>
            </div>
            
            <button class="bet-button" onclick="placeSportsBet('${eventId}', '${selectedTeam}', ${odds})">
                Place Bet
            </button>
        </div>
    `;
    
    const betAmount = document.getElementById('sports-bet-amount');
    betAmount.addEventListener('input', function() {
        calculateSportsPayout(this.value, odds);
    });
    
    document.getElementById('bet-modal-overlay').classList.add('open');
    document.getElementById('bet-modal').classList.add('open');
}

function calculateSportsPayout(betAmount, odds) {
    let payout = 0;
    if (betAmount && !isNaN(betAmount)) {
        const amount = parseFloat(betAmount);
        if (odds > 0) {
            payout = amount * (odds / 100);
        } else {
            payout = amount / (Math.abs(odds) / 100);
        }
    }
    document.getElementById('sports-potential-payout').textContent = formatNumber(payout);
}

function placeSportsBet(eventId, team, odds) {
    const betAmount = parseFloat(document.getElementById('sports-bet-amount').value);
    
    if (!betAmount || betAmount <= 0) {
        alert('Please enter a valid bet amount');
        return;
    }
    
    if (!sportsUserData || sportsUserData.balance < betAmount) {
        alert('Insufficient balance');
        return;
    }
    
    const initData = tg.initData || '';
    
    fetch('/api/sports/place-bet', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            initData: initData,
            eventId: eventId,
            team: team,
            odds: odds,
            betAmount: betAmount
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeSportsBetModal();
            sportsUserData.balance = data.newBalance;
            updateSportsUI();
            alert('Bet placed successfully!');
        } else {
            alert('Error placing bet: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error placing bet:', error);
        alert('Failed to place bet');
    });
}

function closeSportsBetModal() {
    document.getElementById('bet-modal-overlay').classList.remove('open');
    document.getElementById('bet-modal').classList.remove('open');
}

function initSidebar() {
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    
    function openSidebar() {
        sidebar.classList.add('open');
        overlay.classList.add('open');
    }
    
    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.classList.remove('open');
    }
    
    if (menuToggle) {
        menuToggle.addEventListener('click', openSidebar);
    }
    
    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }
    
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', closeSidebar);
    });
}

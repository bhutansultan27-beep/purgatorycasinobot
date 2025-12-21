let sportsUserData = null;
let currentSportFilter = '';

document.addEventListener('DOMContentLoaded', function() {
    loadSportsUserData();
    initSidebar();
    loadSportsOdds();
    initSportsFilters();
});

function initSportsFilters() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            filterBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentSportFilter = this.dataset.sport;
            loadSportsOdds();
        });
    });
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
    const featuredContainer = document.getElementById('featured-games');
    const gamesContainer = document.getElementById('games-list');
    
    featuredContainer.innerHTML = '<div class="featured-loading"><div class="spinner-small"></div><p>Loading featured games...</p></div>';
    gamesContainer.innerHTML = '<div class="empty-state"><i class="fas fa-spinner"></i></div>';
    
    fetch('/api/sports/odds', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ league: currentSportFilter })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Odds response:', data);
        if (data.success && data.odds && data.odds.length > 0) {
            displayFeaturedGames(data.odds.slice(0, 3));
            displayAllGames(data.odds);
            updateEventStats(data.odds.length);
        } else {
            displayEmptyState(featuredContainer);
            displayEmptyState(gamesContainer);
        }
    })
    .catch(error => {
        console.error('Error loading odds:', error);
        displayEmptyState(featuredContainer);
        displayEmptyState(gamesContainer);
    });
}

function updateEventStats(count) {
    const statsEl = document.getElementById('stat-events');
    if (statsEl) {
        statsEl.textContent = count;
    }
}

function displayFeaturedGames(odds) {
    const container = document.getElementById('featured-games');
    container.innerHTML = '';
    
    odds.forEach(event => {
        const eventEl = document.createElement('div');
        eventEl.className = 'featured-game';
        
        const eventTime = new Date(event.commence_time);
        const timeStr = eventTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        eventEl.innerHTML = `
            <div class="game-header">
                <span class="game-league">${event.sport_key || 'SPORTS'}</span>
                <span class="game-time">${timeStr}</span>
            </div>
            <div class="featured-game-teams">
                <div class="team-matchup">${event.home_team}</div>
                <div class="team-matchup">${event.away_team}</div>
            </div>
            <div class="featured-odds">
                <button class="featured-odd-btn" onclick="openSportsBetModal('${event.id}', '${event.home_team}', '${event.home_team}', ${event.home_odds})">
                    ${event.home_team.split(' ').pop()} ${event.home_odds > 0 ? '+' : ''}${event.home_odds}
                </button>
                <button class="featured-odd-btn" onclick="openSportsBetModal('${event.id}', '${event.away_team}', '${event.away_team}', ${event.away_odds})">
                    ${event.away_team.split(' ').pop()} ${event.away_odds > 0 ? '+' : ''}${event.away_odds}
                </button>
            </div>
        `;
        
        container.appendChild(eventEl);
    });
}

function displayAllGames(odds) {
    const container = document.getElementById('games-list');
    container.innerHTML = '';
    
    if (!odds || odds.length === 0) {
        displayEmptyState(container);
        return;
    }
    
    odds.forEach(event => {
        const eventEl = document.createElement('div');
        eventEl.className = 'game-card';
        
        const eventTime = new Date(event.commence_time);
        const timeStr = eventTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const isLive = event.status === 'live';
        
        eventEl.innerHTML = `
            <div class="game-header">
                <span class="game-league">${event.sport_key || 'SPORTS'}</span>
                <span class="game-time-status ${isLive ? 'live' : ''}">
                    ${isLive ? '<i class="fas fa-circle"></i> LIVE' : timeStr}
                </span>
            </div>
            <div class="game-teams">
                <div class="team-row">
                    <span class="team-name">
                        <span class="team-icon">🏠</span>
                        ${event.home_team}
                    </span>
                    <span class="team-odds" onclick="openSportsBetModal('${event.id}', '${event.home_team}', '${event.home_team}', ${event.home_odds})" style="cursor: pointer;">
                        ${event.home_odds > 0 ? '+' : ''}${event.home_odds}
                    </span>
                </div>
                <div class="team-row">
                    <span class="team-name">
                        <span class="team-icon">✈️</span>
                        ${event.away_team}
                    </span>
                    <span class="team-odds" onclick="openSportsBetModal('${event.id}', '${event.away_team}', '${event.away_team}', ${event.away_odds})" style="cursor: pointer;">
                        ${event.away_odds > 0 ? '+' : ''}${event.away_odds}
                    </span>
                </div>
            </div>
        `;
        
        container.appendChild(eventEl);
    });
}

function displayEmptyState(container) {
    container.innerHTML = `
        <div class="empty-state">
            <i class="fas fa-calendar-alt"></i>
            <h3>No games available</h3>
            <p>Check back soon for upcoming matches</p>
        </div>
    `;
}

function openSportsBetModal(eventId, team, selectedTeam, odds) {
    const content = document.getElementById('sports-bet-modal-content');
    
    content.innerHTML = `
        <div>
            <div class="bet-input-group">
                <label class="bet-label">BETTING ON</label>
                <div style="color: #fff; font-size: 16px; font-weight: bold; padding: 12px 0;">
                    ${selectedTeam}
                </div>
            </div>
            
            <div class="bet-input-group">
                <label class="bet-label">ODDS</label>
                <div style="color: #ffa500; font-size: 18px; font-weight: bold; padding: 12px 0;">
                    ${odds > 0 ? '+' : ''}${odds}
                </div>
            </div>
            
            <div class="bet-input-group">
                <label class="bet-label">ENTER BET AMOUNT</label>
                <input type="number" id="sports-bet-amount" class="bet-input" placeholder="Enter amount" min="0.10" step="0.10">
            </div>
            
            <div class="bet-summary">
                <div class="summary-row">
                    <span>To Win:</span>
                    <span>$<span id="sports-potential-payout">0.00</span></span>
                </div>
            </div>
            
            <button class="bet-button" onclick="placeSportsBet('${eventId}', '${selectedTeam}', ${odds})">
                PLACE BET
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
            alert(data.win ? 'Bet won! 🎉' : 'Bet placed - Good luck!');
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

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
    tg.setHeaderColor('#0d0d0f');
    tg.setBackgroundColor('#0d0d0f');
}

function setAvatarPhoto(url) {
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
    
    function openSidebar() {
        sidebar.classList.add('open');
        overlay.classList.add('open');
    }
    
    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.classList.remove('open');
    }
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            if (sidebar.classList.contains('open')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
        
        menuToggle.addEventListener('touchstart', function(e) {
            e.preventDefault();
            if (sidebar.classList.contains('open')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        }, { passive: false });
    }
    
    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
        overlay.addEventListener('touchstart', closeSidebar, { passive: true });
    }
    
    // Use event delegation on the sidebar for all nav items
    if (sidebar) {
        sidebar.addEventListener('click', function(e) {
            const navItem = e.target.closest('.nav-item');
            if (navItem) {
                const href = navItem.getAttribute('href');
                if (href && href.startsWith('#')) {
                    e.preventDefault();
                    closeSidebar();
                    setTimeout(() => {
                        const target = document.querySelector(href);
                        if (target) {
                            target.scrollIntoView({ behavior: 'smooth' });
                        }
                    }, 300);
                } else if (href) {
                    closeSidebar();
                    // Allow default navigation
                }
            }
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

// Live Bets Feature
let liveBets = [];
let lastBetId = 0;
let liveBetsInterval = null;

const gameIcons = {
    'mines': '💣',
    'blackjack': '🃏',
    'baccarat': '👔',
    'keno': '🎯',
    'limbo': '🚀',
    'hilo': '📊',
    'roulette': '🎡',
    'coinflip': '🪙',
    'slots': '🎰',
    'dice': '🎲',
    'connect4': '🔴',
    'crash': '📈',
    'plinko': '🔵',
    'wheel': '🎡'
};

const gameImages = {
    'mines': '/static/images/mines_casino_game_card.png',
    'blackjack': '/static/images/blackjack_casino_game_card.png',
    'baccarat': '/static/images/baccarat_casino_game_card.png',
    'keno': '/static/images/keno_casino_game_card.png',
    'limbo': '/static/images/limbo_casino_game_card.png',
    'hilo': '/static/images/hilo_casino_game_card.png',
    'roulette': '/static/images/roulette_casino_game_card.png',
    'coinflip': '/static/images/coinflip_casino_game_card.png',
    'slots': '/static/images/slots_casino_game_card.png',
    'dice': '/static/images/dice_casino_game_card.png',
    'connect4': '/static/images/connect4_casino_game_card.png',
    'crash': '/static/images/crash_casino_game_card.png',
    'plinko': '/static/images/plinko_casino_game_card.png',
    'wheel': '/static/images/wheel_casino_game_card.png'
};

function initLiveBets() {
    loadLiveBets();
    liveBetsInterval = setInterval(loadLiveBets, 3000);
}

function loadLiveBets() {
    fetch('/api/live-bets?limit=15')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.bets) {
                updateLiveBetsList(data.bets);
            } else {
                updateLiveBetsList([]);
            }
        })
        .catch(error => {
            console.log('Error loading live bets:', error);
            const container = document.getElementById('live-bets-list');
            if (container) {
                container.innerHTML = '<div class="loading-bets">No bets yet. Be the first to play!</div>';
            }
        });
}

function updateLiveBetsList(bets) {
    const container = document.getElementById('live-bets-list');
    if (!container) return;
    
    if (bets.length === 0) {
        container.innerHTML = '<div class="loading-bets">No bets yet. Be the first to play!</div>';
        return;
    }
    
    const newBetIds = bets.map(b => b.id);
    const existingBetIds = liveBets.map(b => b.id);
    const freshBets = newBetIds.filter(id => !existingBetIds.includes(id));
    
    liveBets = bets;
    
    container.innerHTML = bets.map(bet => {
        const isNew = freshBets.includes(bet.id);
        const isWin = bet.payout > 0;
        const gameIcon = gameIcons[bet.game_type.toLowerCase()] || '🎮';
        const username = bet.username || 'Anonymous';
        const initial = username.charAt(0).toUpperCase();
        const payout = isWin ? bet.payout : -bet.wager;
        
        return `
            <div class="live-bet-row ${isNew ? 'new-bet' : ''}" onclick="openBetModal(${bet.id})">
                <div class="bet-user">
                    <div class="bet-user-avatar">${initial}</div>
                    <div>
                        <div class="bet-user-name">${escapeHtml(username)}</div>
                        <div class="bet-id" onclick="event.stopPropagation(); openBetModal(${bet.id})">
                            <i class="fas fa-info-circle"></i>
                            #${bet.id}
                        </div>
                    </div>
                </div>
                <span class="bet-game" data-label="Game">
                    <span class="game-icon">${gameIcon}</span>
                    ${capitalizeFirst(bet.game_type)}
                </span>
                <span class="bet-amount" data-label="Bet">$${formatNumber(bet.wager)}</span>
                <span class="bet-multiplier" data-label="Multi">${bet.multiplier.toFixed(2)}x</span>
                <span class="bet-payout ${isWin ? 'win' : 'loss'}" data-label="Payout">
                    ${isWin ? '+' : ''}$${formatNumber(Math.abs(payout))}
                </span>
            </div>
        `;
    }).join('');
}

function openBetModal(betId) {
    const overlay = document.getElementById('bet-modal-overlay');
    const content = document.getElementById('bet-modal-content');
    
    overlay.classList.add('active');
    content.innerHTML = '<div class="loading-bets">Loading bet details...</div>';
    
    fetch(`/api/bet/${betId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.bet) {
                renderBetDetails(data.bet);
            } else {
                content.innerHTML = '<div class="loading-bets">Bet not found</div>';
            }
        })
        .catch(error => {
            content.innerHTML = '<div class="loading-bets">Error loading bet details</div>';
        });
}

function renderBetDetails(bet) {
    const content = document.getElementById('bet-modal-content');
    const isWin = bet.payout > 0;
    const gameType = bet.game_type.toLowerCase();
    const gameIcon = gameIcons[gameType] || '🎮';
    const gameImage = gameImages[gameType] || '/static/images/logo.png';
    const payout = isWin ? bet.payout : -bet.wager;
    const timestamp = bet.timestamp ? new Date(bet.timestamp).toLocaleString() : 'Unknown';
    const username = bet.username || 'Anonymous';
    const initial = username.charAt(0).toUpperCase();
    
    let resultVisualHtml = renderResultVisual(bet);
    
    content.innerHTML = `
        <div class="bet-game-header">
            <img src="${gameImage}" alt="${capitalizeFirst(bet.game_type)}" class="bet-game-image">
            <div class="bet-game-name">${gameIcon} ${capitalizeFirst(bet.game_type)}</div>
            <div class="bet-id-display">ID #${bet.id}</div>
            <div class="bet-player-info">
                <div class="bet-player-avatar">${initial}</div>
                <span>Placed by <strong>${escapeHtml(username)}</strong></span>
            </div>
            <div class="bet-player-info" style="margin-top: 4px; font-size: 12px;">
                on ${timestamp}
            </div>
        </div>
        
        <div class="bet-stats-row">
            <div class="bet-stat-item">
                <div class="bet-stat-label">Bet</div>
                <div class="bet-stat-value">$${formatNumber(bet.wager)}</div>
            </div>
            <div class="bet-stat-item">
                <div class="bet-stat-label">Multiplier</div>
                <div class="bet-stat-value">${bet.multiplier.toFixed(2)}x</div>
            </div>
            <div class="bet-stat-item">
                <div class="bet-stat-label">Payout</div>
                <div class="bet-stat-value ${isWin ? 'win' : 'loss'}">${isWin ? '+' : ''}$${formatNumber(Math.abs(payout))}</div>
            </div>
        </div>
        
        ${resultVisualHtml}
        
        <div class="bet-actions">
            <a href="/${gameType}" class="play-game-btn">
                <i class="fas fa-play"></i>
                Play ${capitalizeFirst(bet.game_type)}
            </a>
        </div>
    `;
}

function renderResultVisual(bet) {
    const gameType = bet.game_type.toLowerCase();
    const details = bet.details || {};
    const snapshot = bet.game_snapshot || {};
    
    if (gameType === 'limbo') {
        const target = details.target_multiplier || 2;
        const result = details.result_multiplier || details.rolled_multiplier || 1;
        const position = Math.min(Math.max((result / 100) * 100, 0), 100);
        return `
            <div class="bet-result-visual">
                <div class="result-bar-container">
                    <div class="result-bar-labels">
                        <span>0</span>
                        <span>25</span>
                        <span>50</span>
                        <span>75</span>
                        <span>100</span>
                    </div>
                    <div class="result-bar" style="background: linear-gradient(90deg, var(--accent-green) 0%, var(--accent-green) ${target}%, var(--accent-red) ${target}%, var(--accent-red) 100%);">
                        <div class="result-marker" style="left: ${position}%;">${result.toFixed(2)}x</div>
                    </div>
                </div>
                <div class="result-details-grid">
                    <div class="result-detail-box">
                        <div class="result-detail-label">Target</div>
                        <div class="result-detail-value">${target}x</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Roll Result</div>
                        <div class="result-detail-value">${result.toFixed(2)}x</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Win Chance</div>
                        <div class="result-detail-value">${((1/target) * 100).toFixed(2)}%</div>
                    </div>
                </div>
            </div>
        `;
    } else if (gameType === 'coinflip') {
        const choice = details.choice || '?';
        const result = details.result || '?';
        return `
            <div class="bet-result-visual">
                <div class="result-details-grid">
                    <div class="result-detail-box">
                        <div class="result-detail-label">Choice</div>
                        <div class="result-detail-value">${choice}</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Result</div>
                        <div class="result-detail-value">${result}</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Win Chance</div>
                        <div class="result-detail-value">50%</div>
                    </div>
                </div>
            </div>
        `;
    } else if (gameType === 'mines') {
        const gems = details.gems_found || snapshot.gems_found || 0;
        const mines = details.mine_count || details.mines || snapshot.mine_count || 3;
        return `
            <div class="bet-result-visual">
                <div class="result-details-grid">
                    <div class="result-detail-box">
                        <div class="result-detail-label">Gems Found</div>
                        <div class="result-detail-value">${gems} 💎</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Mines</div>
                        <div class="result-detail-value">${mines} 💣</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Safe Tiles</div>
                        <div class="result-detail-value">${25 - mines}</div>
                    </div>
                </div>
            </div>
        `;
    } else if (gameType === 'blackjack') {
        const playerHand = details.player_hand || snapshot.player_value || '?';
        const dealerHand = details.dealer_hand || snapshot.dealer_value || '?';
        return `
            <div class="bet-result-visual">
                <div class="result-details-grid">
                    <div class="result-detail-box">
                        <div class="result-detail-label">Player</div>
                        <div class="result-detail-value">${playerHand}</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Dealer</div>
                        <div class="result-detail-value">${dealerHand}</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Type</div>
                        <div class="result-detail-value">${details.outcome || 'Standard'}</div>
                    </div>
                </div>
            </div>
        `;
    } else if (gameType === 'keno') {
        const hits = details.hits || snapshot.hits || 0;
        const selected = details.numbers_selected || (snapshot.selected ? snapshot.selected.length : 0);
        return `
            <div class="bet-result-visual">
                <div class="result-details-grid">
                    <div class="result-detail-box">
                        <div class="result-detail-label">Selected</div>
                        <div class="result-detail-value">${selected}</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Hits</div>
                        <div class="result-detail-value">${hits}</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Hit Rate</div>
                        <div class="result-detail-value">${selected > 0 ? ((hits/selected)*100).toFixed(0) : 0}%</div>
                    </div>
                </div>
            </div>
        `;
    } else if (gameType === 'roulette') {
        const result = details.result !== undefined ? details.result : '?';
        const color = details.color || '';
        const betType = details.bet_type || '?';
        return `
            <div class="bet-result-visual">
                <div class="result-details-grid">
                    <div class="result-detail-box">
                        <div class="result-detail-label">Result</div>
                        <div class="result-detail-value">${result} ${color}</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Bet Type</div>
                        <div class="result-detail-value">${betType}</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Color</div>
                        <div class="result-detail-value">${color || 'N/A'}</div>
                    </div>
                </div>
            </div>
        `;
    } else if (gameType === 'hilo') {
        const rounds = details.rounds_won || details.streak || 0;
        return `
            <div class="bet-result-visual">
                <div class="result-details-grid">
                    <div class="result-detail-box">
                        <div class="result-detail-label">Rounds Won</div>
                        <div class="result-detail-value">${rounds}</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Last Card</div>
                        <div class="result-detail-value">${details.last_card || '?'}</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Streak</div>
                        <div class="result-detail-value">${rounds}x</div>
                    </div>
                </div>
            </div>
        `;
    } else if (gameType === 'crash') {
        const crashPoint = details.crash_point || details.multiplier || 1;
        const cashoutAt = details.cashout_at || details.cashout || 0;
        return `
            <div class="bet-result-visual">
                <div class="result-details-grid">
                    <div class="result-detail-box">
                        <div class="result-detail-label">Crash Point</div>
                        <div class="result-detail-value">${crashPoint.toFixed(2)}x</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Cashout At</div>
                        <div class="result-detail-value">${cashoutAt > 0 ? cashoutAt.toFixed(2) + 'x' : 'N/A'}</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Result</div>
                        <div class="result-detail-value">${cashoutAt > 0 && cashoutAt < crashPoint ? 'Cashed Out' : 'Crashed'}</div>
                    </div>
                </div>
            </div>
        `;
    } else if (gameType === 'baccarat') {
        const playerScore = details.player_score || details.player || '?';
        const bankerScore = details.banker_score || details.banker || '?';
        const winner = details.winner || details.result || '?';
        return `
            <div class="bet-result-visual">
                <div class="result-details-grid">
                    <div class="result-detail-box">
                        <div class="result-detail-label">Player</div>
                        <div class="result-detail-value">${playerScore}</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Banker</div>
                        <div class="result-detail-value">${bankerScore}</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Winner</div>
                        <div class="result-detail-value">${winner}</div>
                    </div>
                </div>
            </div>
        `;
    } else if (gameType === 'slots') {
        const symbols = details.symbols || details.result || '?';
        return `
            <div class="bet-result-visual">
                <div class="result-details-grid">
                    <div class="result-detail-box" style="grid-column: span 3;">
                        <div class="result-detail-label">Spin Result</div>
                        <div class="result-detail-value" style="font-size: 24px;">${symbols}</div>
                    </div>
                </div>
            </div>
        `;
    } else if (gameType === 'dice') {
        const roll = details.roll || details.result || '?';
        const target = details.target || '?';
        const condition = details.condition || 'over';
        return `
            <div class="bet-result-visual">
                <div class="result-details-grid">
                    <div class="result-detail-box">
                        <div class="result-detail-label">Roll</div>
                        <div class="result-detail-value">${roll}</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Target</div>
                        <div class="result-detail-value">${condition} ${target}</div>
                    </div>
                    <div class="result-detail-box">
                        <div class="result-detail-label">Win Chance</div>
                        <div class="result-detail-value">${details.win_chance || '?'}%</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    return `
        <div class="bet-result-visual">
            <div class="result-details-grid">
                <div class="result-detail-box" style="grid-column: span 3;">
                    <div class="result-detail-label">Game Result</div>
                    <div class="result-detail-value">Game completed</div>
                </div>
            </div>
        </div>
    `;
}

function renderGameSnapshot(gameType, snapshot) {
    const type = gameType.toLowerCase();
    
    if (type === 'blackjack' && snapshot) {
        return renderBlackjackSnapshot(snapshot);
    } else if (type === 'mines' && snapshot) {
        return renderMinesSnapshot(snapshot);
    } else if (type === 'keno' && snapshot) {
        return renderKenoSnapshot(snapshot);
    }
    
    return '';
}

function renderDetailsSnapshot(gameType, details) {
    const type = gameType.toLowerCase();
    
    if (type === 'blackjack' && details.player_hand) {
        return `
            <div class="bet-snapshot">
                <div class="bet-snapshot-title">Game Result</div>
                <div class="blackjack-snapshot">
                    <div>
                        <strong>Player Hand:</strong> ${details.player_hand} (${details.player_value || '?'})
                    </div>
                    <div>
                        <strong>Dealer Hand:</strong> ${details.dealer_hand || '?'} (${details.dealer_value || '?'})
                    </div>
                </div>
            </div>
        `;
    } else if (type === 'mines' && details.gems_found !== undefined) {
        return `
            <div class="bet-snapshot">
                <div class="bet-snapshot-title">Game Result</div>
                <div class="mines-snapshot">
                    <div><strong>Gems Found:</strong> ${details.gems_found} 💎</div>
                    <div><strong>Mines:</strong> ${details.mine_count || details.mines || '?'} 💣</div>
                </div>
            </div>
        `;
    } else if (type === 'keno' && details.hits !== undefined) {
        return `
            <div class="bet-snapshot">
                <div class="bet-snapshot-title">Game Result</div>
                <div class="keno-snapshot">
                    <div><strong>Numbers Selected:</strong> ${details.numbers_selected || '?'}</div>
                    <div><strong>Hits:</strong> ${details.hits}</div>
                </div>
            </div>
        `;
    } else if (type === 'limbo' && details.target_multiplier !== undefined) {
        return `
            <div class="bet-snapshot">
                <div class="bet-snapshot-title">Game Result</div>
                <div>
                    <div><strong>Target:</strong> ${details.target_multiplier}x</div>
                    <div><strong>Result:</strong> ${details.result_multiplier || details.rolled_multiplier}x</div>
                </div>
            </div>
        `;
    } else if (type === 'roulette' && details.result !== undefined) {
        return `
            <div class="bet-snapshot">
                <div class="bet-snapshot-title">Game Result</div>
                <div>
                    <div><strong>Result:</strong> ${details.result} ${details.color || ''}</div>
                    <div><strong>Bet Type:</strong> ${details.bet_type || '?'}</div>
                </div>
            </div>
        `;
    } else if (type === 'coinflip') {
        return `
            <div class="bet-snapshot">
                <div class="bet-snapshot-title">Game Result</div>
                <div>
                    <div><strong>Choice:</strong> ${details.choice || '?'}</div>
                    <div><strong>Result:</strong> ${details.result || '?'}</div>
                </div>
            </div>
        `;
    }
    
    return '';
}

function renderBlackjackSnapshot(snapshot) {
    let playerCards = '';
    let dealerCards = '';
    
    if (snapshot.player_cards) {
        playerCards = snapshot.player_cards.map(card => {
            const isRed = card.includes('♥') || card.includes('♦');
            return `<div class="card-visual ${isRed ? 'red' : 'black'}">${card}</div>`;
        }).join('');
    }
    
    if (snapshot.dealer_cards) {
        dealerCards = snapshot.dealer_cards.map(card => {
            const isRed = card.includes('♥') || card.includes('♦');
            return `<div class="card-visual ${isRed ? 'red' : 'black'}">${card}</div>`;
        }).join('');
    }
    
    return `
        <div class="bet-snapshot">
            <div class="bet-snapshot-title">Game Snapshot</div>
            <div class="blackjack-snapshot">
                <div>
                    <strong>Player (${snapshot.player_value || '?'})</strong>
                    <div class="cards-display">${playerCards || 'N/A'}</div>
                </div>
                <div>
                    <strong>Dealer (${snapshot.dealer_value || '?'})</strong>
                    <div class="cards-display">${dealerCards || 'N/A'}</div>
                </div>
            </div>
        </div>
    `;
}

function renderMinesSnapshot(snapshot) {
    if (!snapshot.grid) return '';
    
    let gridHtml = '';
    for (let i = 0; i < 25; i++) {
        const cell = snapshot.grid[i];
        let cellClass = '';
        let content = '';
        
        if (cell === 'gem') {
            cellClass = 'gem';
            content = '💎';
        } else if (cell === 'mine') {
            cellClass = 'mine';
            content = '💣';
        } else if (cell === 'revealed') {
            cellClass = 'revealed';
            content = '💎';
        } else {
            content = '?';
        }
        
        gridHtml += `<div class="mine-cell ${cellClass}">${content}</div>`;
    }
    
    return `
        <div class="bet-snapshot">
            <div class="bet-snapshot-title">Game Snapshot</div>
            <div class="mines-snapshot">
                <div class="mines-grid">${gridHtml}</div>
                <div><strong>Gems Found:</strong> ${snapshot.gems_found || 0} / ${25 - (snapshot.mine_count || 3)}</div>
            </div>
        </div>
    `;
}

function renderKenoSnapshot(snapshot) {
    if (!snapshot.selected || !snapshot.drawn) return '';
    
    let gridHtml = '';
    for (let i = 1; i <= 40; i++) {
        const isSelected = snapshot.selected.includes(i);
        const isDrawn = snapshot.drawn.includes(i);
        const isHit = isSelected && isDrawn;
        
        let cellClass = '';
        if (isHit) cellClass = 'hit';
        else if (isSelected) cellClass = 'selected';
        else if (isDrawn) cellClass = 'drawn';
        
        gridHtml += `<div class="keno-cell ${cellClass}">${i}</div>`;
    }
    
    return `
        <div class="bet-snapshot">
            <div class="bet-snapshot-title">Game Snapshot</div>
            <div class="keno-snapshot">
                <div class="keno-grid">${gridHtml}</div>
                <div><strong>Hits:</strong> ${snapshot.hits || 0} / ${snapshot.selected.length}</div>
            </div>
        </div>
    `;
}

function closeBetModal() {
    const overlay = document.getElementById('bet-modal-overlay');
    overlay.classList.remove('active');
}

function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize live bets when on home page
if (document.getElementById('live-bets-list')) {
    initLiveBets();
}

// Close modal on overlay click
document.addEventListener('click', function(e) {
    if (e.target.id === 'bet-modal-overlay') {
        closeBetModal();
    }
});

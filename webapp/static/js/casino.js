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
    'connect4': '🔴'
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
            }
        })
        .catch(error => {
            console.log('Error loading live bets:', error);
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
    const gameIcon = gameIcons[bet.game_type.toLowerCase()] || '🎮';
    const payout = isWin ? bet.payout : -bet.wager;
    const timestamp = bet.timestamp ? new Date(bet.timestamp).toLocaleString() : 'Unknown';
    
    let snapshotHtml = '';
    
    if (bet.game_snapshot) {
        snapshotHtml = renderGameSnapshot(bet.game_type, bet.game_snapshot);
    } else if (bet.details) {
        snapshotHtml = renderDetailsSnapshot(bet.game_type, bet.details);
    }
    
    content.innerHTML = `
        <div class="bet-detail-section">
            <h4>Bet Information</h4>
            <div class="bet-detail-grid">
                <div class="bet-detail-item">
                    <div class="bet-detail-label">Bet ID</div>
                    <div class="bet-detail-value">#${bet.id}</div>
                </div>
                <div class="bet-detail-item">
                    <div class="bet-detail-label">Game</div>
                    <div class="bet-detail-value">${gameIcon} ${capitalizeFirst(bet.game_type)}</div>
                </div>
                <div class="bet-detail-item">
                    <div class="bet-detail-label">Player</div>
                    <div class="bet-detail-value">${escapeHtml(bet.username || 'Anonymous')}</div>
                </div>
                <div class="bet-detail-item">
                    <div class="bet-detail-label">Time</div>
                    <div class="bet-detail-value" style="font-size: 13px;">${timestamp}</div>
                </div>
            </div>
        </div>
        
        <div class="bet-detail-section">
            <h4>Results</h4>
            <div class="bet-detail-grid">
                <div class="bet-detail-item">
                    <div class="bet-detail-label">Bet Amount</div>
                    <div class="bet-detail-value">$${formatNumber(bet.wager)}</div>
                </div>
                <div class="bet-detail-item">
                    <div class="bet-detail-label">Multiplier</div>
                    <div class="bet-detail-value">${bet.multiplier.toFixed(2)}x</div>
                </div>
                <div class="bet-detail-item">
                    <div class="bet-detail-label">Result</div>
                    <div class="bet-detail-value ${isWin ? 'win' : 'loss'}">${isWin ? 'WIN' : 'LOSS'}</div>
                </div>
                <div class="bet-detail-item">
                    <div class="bet-detail-label">Payout</div>
                    <div class="bet-detail-value ${isWin ? 'win' : 'loss'}">${isWin ? '+' : ''}$${formatNumber(Math.abs(payout))}</div>
                </div>
            </div>
        </div>
        
        ${snapshotHtml}
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

class BlackjackGame {
    constructor() {
        this.deck = [];
        this.playerHands = [[]];
        this.currentHandIndex = 0;
        this.handBets = [];
        this.dealerHand = [];
        this.balance = 1000;
        this.currentBet = 0;
        this.gameInProgress = false;
        this.isResolving = false;
        this.insurance = false;
        this.insuranceBet = 0;
        this.isSplit = false;
        
        this.tg = window.Telegram?.WebApp;
        
        this.initElements();
        this.initEventListeners();
        this.initTelegram();
    }

    get playerHand() {
        return this.playerHands[this.currentHandIndex];
    }

    set playerHand(hand) {
        this.playerHands[this.currentHandIndex] = hand;
    }

    initElements() {
        this.balanceEl = document.getElementById('balance');
        this.dealerCardsEl = document.getElementById('dealer-cards');
        this.playerCardsEl = document.getElementById('player-cards');
        this.dealerValueEl = document.getElementById('dealer-value');
        this.playerValueEl = document.getElementById('player-value');
        this.betDisplayEl = document.getElementById('bet-display');
        this.bettingSectionEl = document.getElementById('betting-section');
        this.gameControlsEl = document.getElementById('game-controls');
        this.resultOverlayEl = document.getElementById('result-overlay');
        this.resultTitleEl = document.getElementById('result-title');
        this.resultAmountEl = document.getElementById('result-amount');
        this.insuranceModalEl = document.getElementById('insurance-modal');
        this.messageToastEl = document.getElementById('message-toast');
        this.playerSectionEl = document.getElementById('player-section');
        
        this.btnDeal = document.getElementById('btn-deal');
        this.btnClear = document.getElementById('btn-clear');
        this.btnHit = document.getElementById('btn-hit');
        this.btnStand = document.getElementById('btn-stand');
        this.btnDouble = document.getElementById('btn-double');
        this.btnSplit = document.getElementById('btn-split');
        this.btnNewGame = document.getElementById('btn-new-game');
        this.btnInsuranceYes = document.getElementById('btn-insurance-yes');
        this.btnInsuranceNo = document.getElementById('btn-insurance-no');
        this.chips = document.querySelectorAll('.chip');
    }

    initEventListeners() {
        this.chips.forEach(chip => {
            chip.addEventListener('click', () => this.addToBet(parseInt(chip.dataset.value)));
        });
        
        this.btnClear.addEventListener('click', () => this.clearBet());
        this.btnDeal.addEventListener('click', () => this.deal());
        this.btnHit.addEventListener('click', () => this.hit());
        this.btnStand.addEventListener('click', () => this.stand());
        this.btnDouble.addEventListener('click', () => this.doubleDown());
        this.btnSplit.addEventListener('click', () => this.split());
        this.btnNewGame.addEventListener('click', () => this.newGame());
        this.btnInsuranceYes.addEventListener('click', () => this.takeInsurance(true));
        this.btnInsuranceNo.addEventListener('click', () => this.takeInsurance(false));
    }

    initTelegram() {
        if (this.tg) {
            this.tg.ready();
            this.tg.expand();
            
            this.tg.setHeaderColor('#0a0a0a');
            this.tg.setBackgroundColor('#0a0a0a');
            
            if (this.tg.initDataUnsafe?.user) {
                const user = this.tg.initDataUnsafe.user;
                console.log('Telegram user:', user.first_name);
            }
        }
    }

    createDeck() {
        const suits = ['♠', '♥', '♦', '♣'];
        const ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'];
        this.deck = [];
        
        for (let i = 0; i < 8; i++) {
            for (let suit of suits) {
                for (let rank of ranks) {
                    this.deck.push({ rank, suit });
                }
            }
        }
        
        this.shuffleDeck();
    }

    shuffleDeck() {
        for (let i = this.deck.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [this.deck[i], this.deck[j]] = [this.deck[j], this.deck[i]];
        }
    }

    drawCard() {
        if (this.deck.length < 52) {
            this.createDeck();
        }
        return this.deck.pop();
    }

    getCardValue(card) {
        if (['J', 'Q', 'K'].includes(card.rank)) return 10;
        if (card.rank === 'A') return 11;
        return parseInt(card.rank);
    }

    getHandValue(hand) {
        let value = 0;
        let aces = 0;
        
        for (let card of hand) {
            value += this.getCardValue(card);
            if (card.rank === 'A') aces++;
        }
        
        while (value > 21 && aces > 0) {
            value -= 10;
            aces--;
        }
        
        return value;
    }

    isBlackjack(hand) {
        return hand.length === 2 && this.getHandValue(hand) === 21;
    }

    isSoftHand(hand) {
        let value = 0;
        let aces = 0;
        
        for (let card of hand) {
            value += this.getCardValue(card);
            if (card.rank === 'A') aces++;
        }
        
        return aces > 0 && value <= 21;
    }

    addToBet(amount) {
        if (this.gameInProgress) return;
        if (this.currentBet + amount > this.balance) {
            this.showMessage('Insufficient balance');
            return;
        }
        
        this.currentBet += amount;
        this.updateBetDisplay();
        this.btnDeal.disabled = this.currentBet === 0;
        
        if (this.tg) {
            this.tg.HapticFeedback?.impactOccurred('light');
        }
    }

    clearBet() {
        this.currentBet = 0;
        this.updateBetDisplay();
        this.btnDeal.disabled = true;
    }

    updateBetDisplay() {
        this.betDisplayEl.textContent = `$${this.currentBet.toLocaleString()}`;
    }

    updateBalance() {
        this.balanceEl.textContent = `$${this.balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    renderCard(card, hidden = false) {
        const cardEl = document.createElement('div');
        
        if (hidden) {
            cardEl.className = 'card card-back';
            cardEl.dataset.hidden = 'true';
        } else {
            const isRed = ['♥', '♦'].includes(card.suit);
            cardEl.className = `card ${isRed ? 'red' : 'black'}`;
            cardEl.innerHTML = `
                <span class="card-rank">${card.rank}</span>
                <span class="card-suit">${card.suit}</span>
            `;
        }
        
        return cardEl;
    }

    renderHands(hideDealer = true) {
        this.dealerCardsEl.innerHTML = '';
        this.playerCardsEl.innerHTML = '';
        
        this.dealerHand.forEach((card, index) => {
            const hidden = hideDealer && index === 1;
            this.dealerCardsEl.appendChild(this.renderCard(card, hidden));
        });
        
        if (this.isSplit && this.playerHands.length > 1) {
            this.playerHands.forEach((hand, handIndex) => {
                const handContainer = document.createElement('div');
                handContainer.className = `split-hand ${handIndex === this.currentHandIndex ? 'active' : ''}`;
                
                const handLabel = document.createElement('div');
                handLabel.className = 'split-hand-label';
                handLabel.textContent = `Hand ${handIndex + 1}`;
                if (handIndex === this.currentHandIndex && this.gameInProgress) {
                    handLabel.textContent += ' ◄';
                }
                handContainer.appendChild(handLabel);
                
                const cardsDiv = document.createElement('div');
                cardsDiv.className = 'cards-row';
                hand.forEach(card => {
                    cardsDiv.appendChild(this.renderCard(card));
                });
                handContainer.appendChild(cardsDiv);
                
                this.playerCardsEl.appendChild(handContainer);
            });
            
            const values = this.playerHands.map(h => this.getHandValue(h)).join(' / ');
            this.playerValueEl.textContent = values;
        } else {
            this.playerHand.forEach(card => {
                this.playerCardsEl.appendChild(this.renderCard(card));
            });
            this.playerValueEl.textContent = this.getHandValue(this.playerHand);
        }
        
        if (hideDealer && this.dealerHand.length > 0) {
            const firstCardValue = this.getCardValue(this.dealerHand[0]);
            this.dealerValueEl.textContent = firstCardValue;
        } else {
            this.dealerValueEl.textContent = this.getHandValue(this.dealerHand);
        }
    }

    async deal() {
        if (this.currentBet === 0 || this.currentBet > this.balance) return;
        
        this.balance -= this.currentBet;
        this.updateBalance();
        
        this.createDeck();
        this.playerHands = [[]];
        this.currentHandIndex = 0;
        this.handBets = [this.currentBet];
        this.dealerHand = [];
        this.gameInProgress = true;
        this.insurance = false;
        this.insuranceBet = 0;
        this.isSplit = false;
        
        this.bettingSectionEl.style.display = 'none';
        this.gameControlsEl.classList.add('active');
        
        this.playerHands[0].push(this.drawCard());
        this.renderHands();
        await this.delay(300);
        
        this.dealerHand.push(this.drawCard());
        this.renderHands();
        await this.delay(300);
        
        this.playerHands[0].push(this.drawCard());
        this.renderHands();
        await this.delay(300);
        
        this.dealerHand.push(this.drawCard());
        this.renderHands();
        
        if (this.dealerHand[0].rank === 'A') {
            this.offerInsurance();
            return;
        }
        
        this.checkInitialBlackjack();
    }

    offerInsurance() {
        this.insuranceModalEl.classList.add('active');
    }

    takeInsurance(accepted) {
        this.insuranceModalEl.classList.remove('active');
        
        if (accepted && this.balance >= this.currentBet / 2) {
            this.insuranceBet = this.currentBet / 2;
            this.balance -= this.insuranceBet;
            this.updateBalance();
            this.insurance = true;
        }
        
        this.checkInitialBlackjack();
    }

    checkInitialBlackjack() {
        const playerBJ = this.isBlackjack(this.playerHand);
        const dealerBJ = this.isBlackjack(this.dealerHand);
        
        if (dealerBJ) {
            this.renderHands(false);
            
            if (this.insurance) {
                this.balance += this.insuranceBet * 3;
                this.showMessage('Insurance pays!');
            }
            
            if (playerBJ) {
                this.endGame('push', 0);
            } else {
                this.endGame('lose', -this.currentBet);
            }
            return;
        }
        
        if (this.insurance) {
            this.showMessage('No dealer blackjack - insurance lost');
        }
        
        if (playerBJ) {
            this.renderHands(false);
            const winAmount = this.currentBet * 1.5;
            this.endGame('blackjack', winAmount);
            return;
        }
        
        this.updateControls();
    }

    updateControls() {
        const playerValue = this.getHandValue(this.playerHand);
        
        this.btnHit.disabled = playerValue >= 21;
        this.btnStand.disabled = false;
        this.btnDouble.disabled = this.playerHand.length !== 2 || this.balance < this.handBets[this.currentHandIndex];
        
        const canSplit = this.playerHand.length === 2 && 
                        this.getCardValue(this.playerHand[0]) === this.getCardValue(this.playerHand[1]) &&
                        this.balance >= this.handBets[this.currentHandIndex] &&
                        this.playerHands.length < 4;
        this.btnSplit.disabled = !canSplit;
    }

    async hit() {
        if (!this.gameInProgress || this.isResolving) return;
        
        this.playerHand.push(this.drawCard());
        this.renderHands();
        
        if (this.tg) {
            this.tg.HapticFeedback?.impactOccurred('medium');
        }
        
        const playerValue = this.getHandValue(this.playerHand);
        
        if (playerValue > 21) {
            await this.delay(500);
            if (this.isSplit) {
                await this.nextHand();
            } else {
                this.endGame('bust', -this.currentBet);
            }
        } else if (playerValue === 21) {
            await this.delay(300);
            await this.nextHand();
        } else {
            this.updateControls();
        }
    }

    async stand() {
        if (!this.gameInProgress || this.isResolving) return;
        
        if (this.isSplit && this.currentHandIndex < this.playerHands.length - 1) {
            await this.nextHand();
        } else {
            await this.dealerPlay();
        }
    }

    async nextHand() {
        if (this.currentHandIndex < this.playerHands.length - 1) {
            this.currentHandIndex++;
            this.renderHands();
            this.showMessage(`Playing Hand ${this.currentHandIndex + 1}`);
            
            if (this.playerHand.length === 1) {
                await this.delay(300);
                this.playerHand.push(this.drawCard());
                this.renderHands();
            }
            
            this.updateControls();
        } else {
            await this.dealerPlay();
        }
    }

    async dealerPlay() {
        if (this.isResolving) return;
        this.isResolving = true;
        this.disableAllControls();
        
        this.renderHands(false);
        
        while (this.getHandValue(this.dealerHand) < 17) {
            await this.delay(600);
            this.dealerHand.push(this.drawCard());
            this.renderHands(false);
        }
        
        this.determineWinner();
    }
    
    disableAllControls() {
        this.btnHit.disabled = true;
        this.btnStand.disabled = true;
        this.btnDouble.disabled = true;
        this.btnSplit.disabled = true;
    }

    async doubleDown() {
        if (!this.gameInProgress || this.isResolving || this.playerHand.length !== 2) return;
        const bet = this.handBets[this.currentHandIndex];
        if (this.balance < bet) return;
        
        this.balance -= bet;
        this.handBets[this.currentHandIndex] *= 2;
        this.updateBalance();
        
        this.playerHand.push(this.drawCard());
        this.renderHands();
        
        if (this.tg) {
            this.tg.HapticFeedback?.impactOccurred('heavy');
        }
        
        await this.delay(500);
        
        if (this.isSplit && this.currentHandIndex < this.playerHands.length - 1) {
            await this.nextHand();
        } else {
            await this.dealerPlay();
        }
    }

    async split() {
        if (!this.gameInProgress || this.isResolving) return;
        if (this.playerHand.length !== 2) return;
        if (this.getCardValue(this.playerHand[0]) !== this.getCardValue(this.playerHand[1])) return;
        
        const bet = this.handBets[this.currentHandIndex];
        if (this.balance < bet) return;
        
        this.balance -= bet;
        this.updateBalance();
        
        this.isSplit = true;
        
        const secondCard = this.playerHand.pop();
        
        this.playerHands.push([secondCard]);
        this.handBets.push(bet);
        
        this.playerHand.push(this.drawCard());
        this.renderHands();
        
        if (this.tg) {
            this.tg.HapticFeedback?.impactOccurred('heavy');
        }
        
        this.showMessage('Hand split! Playing Hand 1');
        
        this.updateControls();
    }

    determineWinner() {
        const dealerValue = this.getHandValue(this.dealerHand);
        const dealerBust = dealerValue > 21;
        
        let totalWin = 0;
        let results = [];
        
        for (let i = 0; i < this.playerHands.length; i++) {
            const hand = this.playerHands[i];
            const bet = this.handBets[i];
            const playerValue = this.getHandValue(hand);
            const playerBust = playerValue > 21;
            
            if (playerBust) {
                results.push({ hand: i + 1, result: 'bust', amount: -bet });
            } else if (dealerBust) {
                totalWin += bet * 2;
                results.push({ hand: i + 1, result: 'win', amount: bet });
            } else if (playerValue > dealerValue) {
                totalWin += bet * 2;
                results.push({ hand: i + 1, result: 'win', amount: bet });
            } else if (dealerValue > playerValue) {
                results.push({ hand: i + 1, result: 'lose', amount: -bet });
            } else {
                totalWin += bet;
                results.push({ hand: i + 1, result: 'push', amount: 0 });
            }
        }
        
        this.balance += totalWin;
        this.updateBalance();
        
        const totalBets = this.handBets.reduce((a, b) => a + b, 0);
        const netResult = totalWin - totalBets;
        
        if (this.isSplit) {
            const wins = results.filter(r => r.result === 'win').length;
            const losses = results.filter(r => r.result === 'lose' || r.result === 'bust').length;
            
            if (wins > losses) {
                this.showGameResult('win', netResult);
            } else if (losses > wins) {
                this.showGameResult('lose', netResult);
            } else {
                this.showGameResult('push', netResult);
            }
        } else {
            if (netResult > 0) {
                this.showGameResult('win', netResult);
            } else if (netResult < 0) {
                this.showGameResult('lose', netResult);
            } else {
                this.showGameResult('push', 0);
            }
        }
    }

    showGameResult(overallResult, netAmount) {
        this.gameInProgress = false;
        
        if (overallResult === 'win') {
            this.resultTitleEl.textContent = 'YOU WIN!';
            this.resultTitleEl.className = 'result-title win';
            this.resultAmountEl.textContent = `+$${netAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
            
            if (this.tg) {
                this.tg.HapticFeedback?.notificationOccurred('success');
            }
        } else if (overallResult === 'lose') {
            this.resultTitleEl.textContent = 'DEALER WINS';
            this.resultTitleEl.className = 'result-title lose';
            this.resultAmountEl.textContent = `-$${Math.abs(netAmount).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
            
            if (this.tg) {
                this.tg.HapticFeedback?.notificationOccurred('error');
            }
        } else {
            this.resultTitleEl.textContent = 'PUSH';
            this.resultTitleEl.className = 'result-title push';
            this.resultAmountEl.textContent = 'Bet Returned';
            
            if (this.tg) {
                this.tg.HapticFeedback?.notificationOccurred('warning');
            }
        }
        
        this.resultOverlayEl.classList.add('active');
    }

    endGame(result, amount, skipBalanceUpdate = false) {
        this.gameInProgress = false;
        
        if (result === 'win' || result === 'blackjack') {
            if (!skipBalanceUpdate) {
                this.balance += this.currentBet + amount;
            }
            this.resultTitleEl.textContent = result === 'blackjack' ? 'BLACKJACK!' : 'YOU WIN!';
            this.resultTitleEl.className = 'result-title win';
            this.resultAmountEl.textContent = `+$${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
            
            if (this.tg) {
                this.tg.HapticFeedback?.notificationOccurred('success');
            }
        } else if (result === 'lose' || result === 'bust') {
            this.resultTitleEl.textContent = result === 'bust' ? 'BUST!' : 'DEALER WINS';
            this.resultTitleEl.className = 'result-title lose';
            this.resultAmountEl.textContent = `-$${Math.abs(amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
            
            if (this.tg) {
                this.tg.HapticFeedback?.notificationOccurred('error');
            }
        } else {
            if (!skipBalanceUpdate) {
                this.balance += this.currentBet;
            }
            this.resultTitleEl.textContent = 'PUSH';
            this.resultTitleEl.className = 'result-title push';
            this.resultAmountEl.textContent = 'Bet Returned';
            
            if (this.tg) {
                this.tg.HapticFeedback?.notificationOccurred('warning');
            }
        }
        
        if (!skipBalanceUpdate) {
            this.updateBalance();
        }
        this.resultOverlayEl.classList.add('active');
    }

    newGame() {
        this.resultOverlayEl.classList.remove('active');
        this.gameControlsEl.classList.remove('active');
        this.bettingSectionEl.style.display = 'block';
        
        this.currentBet = 0;
        this.updateBetDisplay();
        this.btnDeal.disabled = true;
        
        this.playerHands = [[]];
        this.currentHandIndex = 0;
        this.handBets = [];
        this.dealerHand = [];
        this.isSplit = false;
        this.isResolving = false;
        this.renderHands();
        this.dealerValueEl.textContent = '0';
        this.playerValueEl.textContent = '0';
    }

    showMessage(text) {
        this.messageToastEl.textContent = text;
        this.messageToastEl.classList.add('active');
        
        setTimeout(() => {
            this.messageToastEl.classList.remove('active');
        }, 2000);
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.game = new BlackjackGame();
});

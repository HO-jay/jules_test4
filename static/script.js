
document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = `${window.location.protocol}//${window.location.host}/api/game`;

    const gameConfigDiv = document.getElementById('game-config');
    const gameAreaDiv = document.getElementById('game-area');
    const boardContainer = document.getElementById('board-container');
    const statusMessageEl = document.getElementById('game-message');

    const boardSizeSelect = document.getElementById('board-size');
    const gameModeSelect = document.getElementById('game-mode');
    const aiDifficultySelect = document.getElementById('ai-difficulty');
    const startGameBtn = document.getElementById('start-game-btn');

    const currentPlayerEl = document.getElementById('current-player');
    const capturesBlackEl = document.getElementById('captures-black');
    const capturesWhiteEl = document.getElementById('captures-white');
    const komiDisplayEl = document.getElementById('komi-display');
    const koPointDisplayEl = document.getElementById('ko-point-display');
    const koPointEl = document.getElementById('ko-point');
    const consecutivePassesEl = document.getElementById('consecutive-passes');

    const passTurnBtn = document.getElementById('pass-turn-btn');
    const resignGameBtn = document.getElementById('resign-game-btn');

    // Rules display elements
    const toggleRulesBtn = document.getElementById('toggle-rules-btn');
    const rulesContainer = document.getElementById('rules-container');

    let currentGameData = null;
    let isProcessingAction = false;

    function updateUI(gameData) {
        if (!gameData) { console.error('updateUI called with no gameData'); return; }
        // console.log('Updating UI with gameData:', gameData);
        currentGameData = gameData;

        renderBoard(gameData.board, gameData.board_size);

        let playerText = gameData.current_player;
        if (gameData.is_current_player_ai && !gameData.game_over) {
            playerText += " (AI)";
        } else if (!gameData.is_current_player_ai && !gameData.game_over) {
            playerText += " (Human)";
        }
        currentPlayerEl.textContent = playerText;

        if (gameData.game_over && gameData.final_scores_detailed) {
            capturesBlackEl.textContent = gameData.final_scores_detailed.BLACK.captures;
            capturesWhiteEl.textContent = gameData.final_scores_detailed.WHITE.captures;
        } else if (gameData.captures_display) {
            capturesBlackEl.textContent = gameData.captures_display.BLACK;
            capturesWhiteEl.textContent = gameData.captures_display.WHITE;
        } else {
            capturesBlackEl.textContent = "0";
            capturesWhiteEl.textContent = "0";
        }

        komiDisplayEl.textContent = gameData.komi;

        if (gameData.ko_restriction_point) {
            koPointEl.textContent = `(${gameData.ko_restriction_point[0]}, ${gameData.ko_restriction_point[1]})`;
            koPointDisplayEl.style.display = 'block';
        } else {
            koPointDisplayEl.style.display = 'none';
        }
        consecutivePassesEl.textContent = gameData.consecutive_passes;

        statusMessageEl.textContent = gameData.message || " ";

        if (gameData.game_over) {
            gameConfigDiv.style.display = 'block';
            passTurnBtn.disabled = true;
            resignGameBtn.disabled = true;
            boardContainer.classList.add('game-over');
        } else {
            gameConfigDiv.style.display = 'none';
            gameAreaDiv.style.display = 'block';
            const humanTurn = !gameData.is_current_player_ai && !isProcessingAction;
            passTurnBtn.disabled = !humanTurn;
            resignGameBtn.disabled = !humanTurn;
            boardContainer.classList.remove('game-over');
        }
        isProcessingAction = false;
    }

    function renderBoard(boardGrid, boardSize) {
        boardContainer.innerHTML = '';
        const cellSize = Math.max(20, Math.floor(Math.min(window.innerWidth * 0.8, window.innerHeight * 0.5) / boardSize) );
        boardContainer.style.gridTemplateColumns = `repeat(${boardSize}, ${cellSize}px)`;
        boardContainer.style.gridTemplateRows = `repeat(${boardSize}, ${cellSize}px)`;
        boardContainer.style.width = `${boardSize * cellSize}px`;
        boardContainer.style.height = `${boardSize * cellSize}px`;

        const hoshiPoints = {
            9: [[2,2], [2,6], [4,4], [6,2], [6,6]],
            13: [[3,3], [3,9], [6,6], [9,3], [9,9]],
            19: [[3,3], [3,9], [3,15], [9,3], [9,9], [9,15], [15,3], [15,9], [15,15]]
        };
        const currentHoshi = hoshiPoints[boardSize] || [];

        for (let r = 0; r < boardSize; r++) {
            for (let c = 0; c < boardSize; c++) {
                const intersection = document.createElement('div');
                intersection.classList.add('intersection');
                intersection.dataset.row = r;
                intersection.dataset.col = c;
                intersection.style.width = `${cellSize}px`;
                intersection.style.height = `${cellSize}px`;

                if (currentHoshi.some(p => p[0] === r && p[1] === c)) {
                    intersection.classList.add('hoshi');
                }

                const stoneType = boardGrid[r][c];
                if (stoneType) {
                    const stoneDiv = document.createElement('div');
                    stoneDiv.classList.add('stone', stoneType);
                    intersection.appendChild(stoneDiv);
                } else {
                    if (currentGameData && !currentGameData.game_over && !currentGameData.is_current_player_ai) {
                         intersection.addEventListener('click', handleIntersectionClick);
                    } else {
                        intersection.style.cursor = 'default';
                    }
                }
                boardContainer.appendChild(intersection);
            }
        }
    }

    async function handleApiCall(endpoint, method = 'POST', body = null) {
        if (isProcessingAction && method === 'POST') {
            statusMessageEl.textContent = "Previous action still processing. Please wait.";
            return;
        }
        isProcessingAction = true;
        statusMessageEl.textContent = "Processing...";
        passTurnBtn.disabled = true;
        resignGameBtn.disabled = true;

        try {
            const options = { method };
            if (body) {
                options.headers = { 'Content-Type': 'application/json' };
                options.body = JSON.stringify(body);
            }
            const response = await fetch(endpoint, options);
            const gameData = await response.json();

            if (!response.ok) {
                throw new Error(gameData.error || `HTTP error! status: ${response.status}`);
            }
            updateUI(gameData);
        } catch (error) {
            console.error(`Error with ${endpoint}:`, error);
            statusMessageEl.textContent = `Error: ${error.message}`;
            isProcessingAction = false;
            if(currentGameData && !currentGameData.game_over) {
                const humanTurn = !currentGameData.is_current_player_ai;
                passTurnBtn.disabled = !humanTurn;
                resignGameBtn.disabled = !humanTurn;
            } else if (!currentGameData) { // If error happened before game even started
                 passTurnBtn.disabled = true; resignGameBtn.disabled = true;
            }
        }
    }

    async function handleIntersectionClick(event) {
        if (isProcessingAction || (currentGameData && currentGameData.is_current_player_ai)) return;
        const row = event.currentTarget.dataset.row;
        const col = event.currentTarget.dataset.col;
        await handleApiCall(`${API_BASE_URL}/move`, 'POST', { row: parseInt(row), col: parseInt(col) });
    }

    startGameBtn.addEventListener('click', () => {
        handleApiCall(`${API_BASE_URL}/start`, 'POST', {
            board_size: parseInt(boardSizeSelect.value),
            mode: gameModeSelect.value,
            ai_difficulty: aiDifficultySelect.value
        });
    });

    passTurnBtn.addEventListener('click', () => {
        if (isProcessingAction || (currentGameData && currentGameData.is_current_player_ai)) return;
        handleApiCall(`${API_BASE_URL}/pass`, 'POST');
    });

    resignGameBtn.addEventListener('click', () => {
        if (isProcessingAction && (currentGameData && currentGameData.is_current_player_ai)) return; // AI cannot resign via button
        if (!confirm("Are you sure you want to resign?")) {
            return;
        }
        handleApiCall(`${API_BASE_URL}/resign`, 'POST');
    });

    // Rules Toggle Functionality
    if (toggleRulesBtn && rulesContainer) {
        toggleRulesBtn.addEventListener('click', () => {
            if (rulesContainer.style.display === 'none') {
                rulesContainer.style.display = 'block';
                toggleRulesBtn.textContent = 'Hide Game Rules';
            } else {
                rulesContainer.style.display = 'none';
                toggleRulesBtn.textContent = 'Show Game Rules';
            }
        });
    } else {
        console.warn("Rules toggle button or container not found.");
    }

    gameAreaDiv.style.display = 'none';
    gameConfigDiv.style.display = 'block';
});

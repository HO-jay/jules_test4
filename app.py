
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game import Game, Stone
from ai import AIOpponent

app = Flask(__name__)
CORS(app)

current_game_instance = None

def get_game_state_dict(game_instance):
    if not game_instance:
        return None

    board_data = []
    for r_idx in range(game_instance.board.size):
        row_data = []
        for c_idx in range(game_instance.board.size):
            stone = game_instance.board.get_stone(r_idx,c_idx)
            row_data.append(stone.name if stone != Stone.EMPTY else None)
        board_data.append(row_data)

    current_scores_or_status = game_instance.get_scores()

    state = {
        'board': board_data,
        'board_size': game_instance.board.size,
        'current_player': game_instance.current_player.name, # current_player is always up-to-date from game_instance
        'is_current_player_ai': game_instance.get_current_ai_player() is not None,
        'captures_display': { # For ongoing game display
            'BLACK': current_scores_or_status.get('black_captures_current', 0),
            'WHITE': current_scores_or_status.get('white_captures_current', 0)
        },
        'ko_restriction_point': current_scores_or_status.get('ko_restriction_point'),
        'consecutive_passes': current_scores_or_status.get('consecutive_passes', game_instance.consecutive_passes),
        'game_over': game_instance.game_over,
        'final_scores_detailed': None,
        'winner': None,
        'komi': current_scores_or_status.get('komi_setting', game_instance.komi), # Use komi_setting if game not over
        'message': current_scores_or_status.get('status', '')
    }

    if game_instance.game_over:
        # get_scores() returns detailed territory scores when game_over
        state['final_scores_detailed'] = {
            'BLACK': {
                'total': current_scores_or_status.get('black_score_total', "N/A"),
                'territory': current_scores_or_status.get('black_score_territory', "N/A"),
                'captures': current_scores_or_status.get('black_score_captures', "N/A")
            },
            'WHITE': {
                'total': current_scores_or_status.get('white_score_total', "N/A"),
                'territory': current_scores_or_status.get('white_score_territory', "N/A"),
                'captures': current_scores_or_status.get('white_score_captures', "N/A"),
                'komi_applied': current_scores_or_status.get('komi_applied', game_instance.komi)
            }
        }

        b_total = current_scores_or_status.get('black_score_total')
        w_total = current_scores_or_status.get('white_score_total')

        # Handle cases where scores might be strings (e.g., "Won by Resignation")
        if isinstance(b_total, str) or isinstance(w_total, str):
            if "Won by Resignation" == b_total : state['winner'] = Stone.BLACK.name
            elif "Won by Resignation" == w_total : state['winner'] = Stone.WHITE.name
            # If one resigned, the other won.
            elif "Resigned" in b_total: state['winner'] = Stone.WHITE.name
            elif "Resigned" in w_total: state['winner'] = Stone.BLACK.name

        elif isinstance(b_total, (int, float)) and isinstance(w_total, (int, float)):
            if b_total > w_total: state['winner'] = Stone.BLACK.name
            elif w_total > b_total: state['winner'] = Stone.WHITE.name
            else: state['winner'] = "DRAW"

        current_path = request.path if request else "" # Get current request path safely
        if current_path == '/api/game/resign':
             # Resign endpoint will set its own specific message including winner
             # The message set by resign might already be in state['message'] if get_scores was called by resign
             pass
        elif state['winner'] or state['final_scores_detailed']['BLACK']['total'] != "N/A": # If scores are calculated
            msg = f"Game Over. "
            if state['winner'] and state['winner'] != "DRAW": msg += f"Winner: {state['winner']}. "
            elif state['winner'] == "DRAW": msg += "Result is a Draw. "

            # Append score details
            bsd = state['final_scores_detailed']['BLACK']
            wsd = state['final_scores_detailed']['WHITE']
            msg += f"Scores - BLACK: {bsd['total']} (T:{bsd['territory']}, C:{bsd['captures']}) "
            msg += f"WHITE: {wsd['total']} (T:{wsd['territory']}, C:{wsd['captures']}, Komi:{wsd['komi_applied']})"
            state['message'] = msg
        else: # Game over but no scores yet (should not happen if calculate_territory_scores is called)
            state['message'] = "Game Over. Scores pending calculation."

    return state

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/game/start', methods=['POST'])
def start_game():
    global current_game_instance; data = request.json
    board_size = data.get('board_size', 19); mode = data.get('mode', 'hvh'); ai_difficulty = data.get('ai_difficulty', 'easy')
    pb_ai, pw_ai = (mode == 'hva_w' or mode == 'ava'), (mode == 'hva_b' or mode == 'ava')
    current_game_instance = Game(board_size=board_size, komi=6.5, player_black_is_ai=pb_ai, player_white_is_ai=pw_ai, ai_difficulty=ai_difficulty)

    action_message = f"Game started (Mode: {mode}, Size: {board_size}, AI Diff: {ai_difficulty}). "
    if current_game_instance.get_current_ai_player() and current_game_instance.current_player == Stone.BLACK:
        _, ai_msg = current_game_instance.request_ai_move()
        action_message += f"AI (Black) response: {ai_msg} "

    state = get_game_state_dict(current_game_instance)
    if state:
        if not state['game_over']: action_message += f"{state['current_player']} to move."
        else: action_message += state.get('message','') # Append game over message if AI vs AI ended quickly
        state['message'] = action_message.strip()
    return jsonify(state or {"error": "Could not start game"})

@app.route('/api/game/state', methods=['GET'])
def game_state_api():
    global current_game_instance
    if current_game_instance is None: return jsonify({"error": "No game started"}), 404
    return jsonify(get_game_state_dict(current_game_instance))

@app.route('/api/game/move', methods=['POST'])
def make_move_api():
    global current_game_instance
    if not current_game_instance or current_game_instance.game_over:
        return jsonify({"error": "No active game or game is over", "game_state": get_game_state_dict(current_game_instance)}), 400
    data = request.json; row, col = data.get('row'), data.get('col')
    if row is None or col is None: return jsonify({"error": "Row/col missing", "game_state": get_game_state_dict(current_game_instance)}), 400
    try: row, col = int(row), int(col)
    except ValueError: return jsonify({"error": "Row/col must be int", "game_state": get_game_state_dict(current_game_instance)}), 400

    if current_game_instance.get_current_ai_player():
        return jsonify({"error": "AI's turn", "game_state": get_game_state_dict(current_game_instance)}), 400

    player_making_move = current_game_instance.current_player.name
    success, move_msg = current_game_instance.make_move(row, col)
    action_message = f"Player {player_making_move}: {move_msg}. "

    if success and not current_game_instance.game_over and current_game_instance.get_current_ai_player():
        _, ai_msg = current_game_instance.request_ai_move()
        action_message += f"AI response: {ai_msg}"

    state = get_game_state_dict(current_game_instance)
    if state: state['message'] = action_message.strip() + (" " + state.get('message', '') if state.get('game_over') else "")
    return jsonify(state or {"error": "Error processing move"})

@app.route('/api/game/pass', methods=['POST'])
def pass_turn_api():
    global current_game_instance
    if not current_game_instance or current_game_instance.game_over: return jsonify({"error": "No active game or game is over"}), 400
    if current_game_instance.get_current_ai_player(): return jsonify({"error": "AI's turn"}), 400

    success, pass_msg = current_game_instance.pass_turn()
    action_message = pass_msg # Message from game.pass_turn() is comprehensive

    if success and not current_game_instance.game_over and current_game_instance.get_current_ai_player():
        _, ai_msg = current_game_instance.request_ai_move()
        action_message += f" AI response: {ai_msg}"

    state = get_game_state_dict(current_game_instance)
    if state: state['message'] = action_message.strip() + (" " + state.get('message', '') if state.get('game_over') and state.get('message') else "")
    return jsonify(state)

@app.route('/api/game/resign', methods=['POST'])
def resign_game_api():
    global current_game_instance
    if not current_game_instance or current_game_instance.game_over: return jsonify({"error": "No active game or game is over"}), 400

    resigning_player = current_game_instance.current_player
    current_game_instance.game_over = True
    winner = Stone.WHITE if resigning_player == Stone.BLACK else Stone.BLACK

    current_game_instance.final_scores = {} # Clear any calculated scores
    current_game_instance.final_scores[Stone.BLACK] = {'total': "Lost by Resignation", 'territory':0,'captures':0}
    current_game_instance.final_scores[Stone.WHITE] = {'total': "Lost by Resignation", 'territory':0,'captures':0, 'komi_added':0}
    current_game_instance.final_scores[winner]['total'] = "Won by Resignation"

    state = get_game_state_dict(current_game_instance)
    state['message'] = f"Player {resigning_player.name} resigned. Winner: {winner.name}."
    # Winner is already set by get_game_state_dict based on string scores
    return jsonify(state)

if __name__ == '__main__':
    print("Starting Flask server for Baduk game API...")
    app.run(debug=True, port=5001, use_reloader=False)

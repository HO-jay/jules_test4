
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
    if not game_instance: return None
    board_data = [[(stone.name if stone != Stone.EMPTY else None) for stone in row] for row in game_instance.board._grid]
    state = {
        'board': board_data, 'board_size': game_instance.board.size,
        'current_player': game_instance.current_player.name,
        'is_current_player_ai': game_instance.get_current_ai_player() is not None,
        'captures': {'BLACK': game_instance.captures.get(Stone.BLACK, 0), 'WHITE': game_instance.captures.get(Stone.WHITE, 0)},
        'ko_restriction_point': game_instance.ko_restriction_point,
        'consecutive_passes': game_instance.consecutive_passes,
        'game_over': game_instance.game_over, 'final_scores': None, 'winner': None,
        'komi': game_instance.komi, 'message': ""
    }
    if game_instance.game_over:
        scores_from_game = game_instance.get_scores()
        state['final_scores'] = {'BLACK': scores_from_game.get('black_score', "N/A"), 'WHITE': scores_from_game.get('white_score', "N/A")}
        black_s, white_s = scores_from_game.get('black_score'), scores_from_game.get('white_score')
        if isinstance(black_s, str) and "Resignation" in black_s: state['winner'] = Stone.WHITE.name if "Lost" in black_s or "Resigned" in black_s else Stone.BLACK.name
        elif isinstance(white_s, str) and "Resignation" in white_s: state['winner'] = Stone.BLACK.name if "Lost" in white_s or "Resigned" in white_s else Stone.WHITE.name
        elif isinstance(black_s, (int, float)) and isinstance(white_s, (int, float)):
            if black_s > white_s: state['winner'] = Stone.BLACK.name
            elif white_s > black_s: state['winner'] = Stone.WHITE.name
            else: state['winner'] = "DRAW"
        state['message'] = "Game Over. "
        if state['winner'] and state['winner'] != "DRAW": state['message'] += f"Winner: {state['winner']}."
        elif state['winner'] == "DRAW": state['message'] += "Result is a Draw."
        elif state['final_scores']['BLACK'] != "N/A": state['message'] += "Scores calculated."
    return state

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/game/start', methods=['POST'])
def start_game():
    global current_game_instance; data = request.json
    board_size, mode, ai_difficulty = data.get('board_size', 19), data.get('mode', 'hvh'), data.get('ai_difficulty', 'easy')
    pb_ai, pw_ai = (mode == 'hva_w' or mode == 'ava'), (mode == 'hva_b' or mode == 'ava')
    current_game_instance = Game(board_size=board_size, komi=6.5, player_black_is_ai=pb_ai, player_white_is_ai=pw_ai, ai_difficulty=ai_difficulty)
    msg = f"Game started (Mode: {mode}, Size: {board_size}, AI Diff: {ai_difficulty}). "
    if current_game_instance.get_current_ai_player() and current_game_instance.current_player == Stone.BLACK:
        current_game_instance.request_ai_move(); msg += "AI (Black) has moved. "
    state = get_game_state_dict(current_game_instance)
    if state:
        if not state['game_over']: msg += f"{state['current_player']} to move."
        state['message'] = msg
    return jsonify(state or {"error": "Could not start game"})

@app.route('/api/game/state', methods=['GET'])
def game_state_api():
    if current_game_instance is None: return jsonify({"error": "No game started"}), 404
    return jsonify(get_game_state_dict(current_game_instance))

@app.route('/api/game/move', methods=['POST'])
def make_move_api():
    global current_game_instance
    if not current_game_instance or current_game_instance.game_over: return jsonify({"error": "No active game or game is over"}), 400
    data = request.json; row, col = data.get('row'), data.get('col')
    if row is None or col is None: return jsonify({"error": "Row/col missing"}), 400
    try: row, col = int(row), int(col)
    except ValueError: return jsonify({"error": "Row/col must be int"}), 400
    if current_game_instance.get_current_ai_player(): return jsonify({"error": "AI's turn"}), 400

    player_name_before_move = current_game_instance.current_player.name
    success = current_game_instance.make_move(row, col)
    msg = ""
    if not success:
        msg = f"Invalid move by {player_name_before_move} at ({row},{col}). "
        if current_game_instance.ko_restriction_point == (row,col): # Check if it was Ko
             msg += "Violates Ko rule. "
        # else: Game class prints other errors to console. API consumer sees generic fail.
    else:
        msg = f"Move at ({row},{col}) by {player_name_before_move} successful. "
        if not current_game_instance.game_over and current_game_instance.get_current_ai_player():
            current_game_instance.request_ai_move()
            # Message about AI's response will be part of the new state's message

    state = get_game_state_dict(current_game_instance)
    if state: state['message'] = msg + state.get('message', '') # Prepend action message
    return jsonify(state or {"error": "Error processing move"})

@app.route('/api/game/pass', methods=['POST'])
def pass_turn_api():
    global current_game_instance
    if not current_game_instance or current_game_instance.game_over: return jsonify({"error": "No active game or game is over"}), 400
    if current_game_instance.get_current_ai_player(): return jsonify({"error": "AI's turn"}), 400

    passed_player_name = current_game_instance.current_player.name
    current_game_instance.pass_turn()
    msg = f"Player {passed_player_name} passed. "
    if not current_game_instance.game_over and current_game_instance.get_current_ai_player():
        current_game_instance.request_ai_move()
    state = get_game_state_dict(current_game_instance)
    if state: state['message'] = msg + state.get('message', '')
    return jsonify(state)

@app.route('/api/game/resign', methods=['POST'])
def resign_game_api():
    global current_game_instance
    if not current_game_instance or current_game_instance.game_over: return jsonify({"error": "No active game or game is over"}), 400
    resigning_player = current_game_instance.current_player
    current_game_instance.game_over = True
    winner = Stone.WHITE if resigning_player == Stone.BLACK else Stone.BLACK
    current_game_instance.final_scores = {}
    current_game_instance.final_scores['black_score'] = "Won by Resignation" if winner == Stone.BLACK else "Lost by Resignation"
    current_game_instance.final_scores['white_score'] = "Won by Resignation" if winner == Stone.WHITE else "Lost by Resignation"
    state = get_game_state_dict(current_game_instance)
    state['message'] = f"Player {resigning_player.name} resigned. Winner: {winner.name}."
    return jsonify(state)

if __name__ == '__main__':
    print("Starting Flask server for Baduk game API...")
    app.run(debug=True, port=5001, use_reloader=False)

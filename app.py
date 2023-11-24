from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
import json
from datetime import datetime
import os

app = Flask(__name__)
socketio = SocketIO(app, namespace='/test')
CORS(app)

DISCORD_CLIENT_ID = '985523546652545044'
DISCORD_CLIENT_SECRET = 'RkgN0ieLknlny8eeCFpj4iVsXyILDojA'
DISCORD_REDIRECT_URI = 'http://localhost/'
DISCORD_AUTHORIZE_URL = 'https://discord.com/api/oauth2/authorize'

DISCORD_WEBHOOK_URL = 'https://ptb.discord.com/api/webhooks/1177449124170309692/G8BlkdmQBCRHVh0bXiNtxh_TY4a35fPabfEXLNM8r8UnOarrULX9kcf2sFZ3QvbSqIPW'

@app.route('/')
def index():
    script_dir = os.path.dirname(__file__)
    rel_path = 'index.html'
    abs_file_path = os.path.join(script_dir, rel_path)
    with open(abs_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

@app.route('/login')
def login():
    discord_login_url = f'{DISCORD_AUTHORIZE_URL}?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope=identify email'
    return redirect(discord_login_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        token_url = 'https://discord.com/api/oauth2/token'
        token_data = {
            'client_id': DISCORD_CLIENT_ID,
            'client_secret': DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': DISCORD_REDIRECT_URI,
            'scope': 'identify email'
        }
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()

        user_url = 'https://discord.com/api/users/@me'
        headers = {'Authorization': f'Bearer {token_json["access_token"]}'}
        user_response = requests.get(user_url, headers=headers)
        user_json = user_response.json()

        discord_id = user_json.get('id')

        return f"Logged in! Discord ID: {discord_id}"

    return 'Error during login'

@app.route('/submit', methods=['POST'])
def submit_ticket():
    username = request.form.get('username')
    message = request.form.get('message')

    # 디스코드 아이디를 수집
    discord_id = request.form.get('discord_id')

    send_discord_webhook(username, message, discord_id)
    socketio.emit('new_ticket', {'username': username, 'message': message}, namespace='/test')

    return 'Success'

@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my_response', {'data': 'Connected'})

def send_discord_webhook(username, message, discord_id=None):
    embed = {
        'title': '새로운 문의가 등록되었습니다!',
        'description': f'**유저:** {username}\n**내용:** {message}\n**고객 아이디:** {discord_id}',
        'color': 0x166cea,
        'timestamp': str(datetime.utcnow()),
    }

    payload = {
        'embeds': [embed],
    }

    headers = {'Content-Type': 'application/json'}
    response = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(payload), headers=headers)

    print(response.status_code, response.text)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=80)

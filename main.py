import sqlite3
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, request, jsonify, render_template_string, Response

app = Flask(__name__)
app.secret_key = "nijinohara-secret-key"

# 管理者ログイン情報
ADMIN_USER = "kaitojpjp"
ADMIN_PASS = "nijinohara1212"

# Vercelの一時ディレクトリ(/tmp)内にデータベースを作成
DB_NAME = "/tmp/lottery.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roblox_name TEXT UNIQUE NOT NULL,
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        user_agent TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lottery_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        participant_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE
    )
    ''')
    conn.commit()
    conn.close()

@app.before_request
def ensure_db():
    init_db()

def check_admin_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASS

def authenticate():
    return Response(
        '管理者ログインが必要です。', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

# --- フロントエンド HTML ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>虹の原BRT抽選サイト</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: rgba(23, 31, 50, 0.7);
            --border-color: rgba(255, 255, 255, 0.1);
            --accent-color: #6366f1;
            --text-color: #f3f4f6;
            --text-muted: #9ca3af;
        }
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0; padding: 0;
            min-height: 100vh;
        }
        .ticker-wrap {
            width: 100%;
            background: rgba(239, 68, 68, 0.2);
            border-bottom: 1px solid rgba(239, 68, 68, 0.4);
            overflow: hidden; white-space: nowrap; padding: 10px 0;
        }
        .ticker-move {
            display: inline-block; white-space: nowrap; padding-left: 100%;
            animation: ticker 20s linear infinite; font-weight: bold; color: #fca5a5;
        }
        @keyframes ticker { 0% { transform: translate3d(0, 0, 0); } 100% { transform: translate3d(-100%, 0, 0); } }

        .header-nav {
            display: flex; justify-content: space-between; align-items: center;
            padding: 15px 30px; background: rgba(15, 23, 42, 0.8);
        }
        .container { max-width: 500px; margin: 40px auto; padding: 0 20px; }
        .glass-card {
            background: var(--card-bg); backdrop-filter: blur(12px);
            border: 1px solid var(--border-color); border-radius: 16px; padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
        }
        .btn {
            display: block; width: 100%; padding: 12px; background-color: var(--accent-color);
            color: white; border: none; border-radius: 8px; font-size: 1rem; font-weight: bold;
            cursor: pointer; transition: 0.3s; text-align: center; text-decoration: none; box-sizing: border-box;
        }
        .btn:hover { background-color: #4f46e5; }
        .input-group { margin-bottom: 20px; }
        .input-group label { display: block; margin-bottom: 8px; color: var(--text-muted); }
        .input-control {
            width: 100%; padding: 12px; background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color); border-radius: 8px; color: white; box-sizing: border-box;
        }
        .checkbox-group { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
        .checkbox-item { display: flex; align-items: center; gap: 10px; font-size: 0.9rem; }
    </style>
</head>
<body>

    <div class="ticker-wrap">
        <div class="ticker-move">不正はばれます。抽選権を剥奪します。by某先輩</div>
    </div>

    <header class="header-nav">
        <div style="font-weight:bold;"><i class="fa-solid fa-bus"></i> 虹の原BRT抽選サイト</div>
        <a href="/admin" class="btn" style="width: auto; padding: 6px 16px; font-size:0.85rem;">管理者ログイン</a>
    </header>

    <div class="container">
        <div class="glass-card">
            {% if show_results %}
                <h2><i class="fa-solid fa-trophy"></i> 抽選結果</h2>
                <h3>当選者 (20名)</h3>
                <ul>
                    {% for w in winners %}
                        <li>Roblox: {{ w }}</li>
                    {% endfor %}
                </ul>
                <h3>補欠 (5名)</h3>
                <ul>
                    {% for s in substitutes %}
                        <li>Roblox: {{ s }}</li>
                    {% endfor %}
                </ul>
            {% else %}
                <p style="text-align: center; color: var(--text-muted); margin-bottom: 20px;">
                    <i class="fa-solid fa-clock"></i> 抽選結果は <strong>2026年8月7日 10:00</strong> に公開されます。
                </p>
                <hr style="border-color: var(--border-color); margin-bottom: 25px;">

                <div id="form-container">
                    <form id="joinForm">
                        <div class="input-group">
                            <label for="roblox_name">Roblox ネーム <span style="color:red">*</span></label>
                            <input type="text" id="roblox_name" name="roblox_name" class="input-control" placeholder="ユーザー名を入力" required>
                        </div>

                        <div class="checkbox-group">
                            <label class="checkbox-item"><input type="checkbox" required> 抽選するものは13歳以上であること</label>
                            <label class="checkbox-item"><input type="checkbox" required> 過去に警告歴がないこと</label>
                            <label class="checkbox-item"><input type="checkbox" required> イベントに参加できること</label>
                        </div>

                        <button type="submit" class="btn">抽選に参加する</button>
                    </form>
                </div>
            {% endif %}
        </div>
    </div>

    <script>
        const form = document.getElementById('joinForm');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const robloxName = document.getElementById('roblox_name').value;

                const res = await fetch('/api/join', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ roblox_name: robloxName })
                });

                const data = await res.json();
                if (res.ok) {
                    document.getElementById('form-container').innerHTML = `
                        <div style="text-align:center; padding: 20px; color:#10B981;">
                            <h3>🎉 参加完了</h3>
                            <p>参加ありがとうございました。</p>
                        </div>
                    `;
                } else {
                    alert(data.message || 'エラーが発生しました。');
                }
            });
        }
    </script>
</body>
</html>
"""

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>管理画面 - 虹の原BRT</title>
    <style>
        body { background: #0b0f19; color: white; font-family: sans-serif; padding: 30px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: rgba(255,255,255,0.05); }
        th, td { padding: 10px; border: 1px solid #333; text-align: left; }
        .btn-draw { background: #10B981; color: white; border: none; padding: 10px 20px; cursor: pointer; border-radius: 5px; }
    </style>
</head>
<body>
    <h2>管理ダッシュボード</h2>
    <p>現在の参加人数: {{ participants|length }} 名</p>

    <form action="/admin/draw" method="POST" onsubmit="return confirm('抽選を実行しますか？');">
        <button type="submit" class="btn-draw">抽選（再抽選）を実行する</button>
    </form>

    <h3>参加者一覧</h3>
    <table>
        <tr><th>ID</th><th>Robloxネーム</th><th>参加日時</th><th>IPアドレス</th></tr>
        {% for p in participants %}
        <tr>
            <td>{{ p[0] }}</td>
            <td>{{ p[1] }}</td>
            <td>{{ p[2] }}</td>
            <td>{{ p[3] }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

# --- ルーティング ---

# ファビコン要求のエラー防止
@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def index():
    target_time = datetime(2026, 8, 7, 10, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo"))
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    show_results = now >= target_time

    winners, substitutes = [], []
    if show_results:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT p.roblox_name, lr.role FROM lottery_results lr JOIN participants p ON lr.participant_id = p.id")
        for row in cur.fetchall():
            if row[1] == 'winner': winners.append(row[0])
            else: substitutes.append(row[0])
        conn.close()

    return render_template_string(HTML_TEMPLATE, show_results=show_results, winners=winners, substitutes=substitutes)

@app.route('/api/join', methods=['POST'])
def join():
    data = request.get_json()
    roblox_name = data.get('roblox_name', '').strip()

    if not roblox_name:
        return jsonify({'message': 'Robloxネームを入力してください。'}), 400

    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')

    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO participants (roblox_name, ip_address, user_agent) VALUES (?, ?, ?)",
            (roblox_name, ip_address, user_agent)
        )
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'message': 'このRobloxネームは既に送信済みです。'}), 400

@app.route('/admin')
def admin():
    auth_info = request.authorization
    if not auth_info or not check_admin_auth(auth_info.username, auth_info.password):
        return authenticate()

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, roblox_name, joined_at, ip_address FROM participants ORDER BY id DESC")
    participants = cur.fetchall()
    conn.close()

    return render_template_string(ADMIN_TEMPLATE, participants=participants)

@app.route('/admin/draw', methods=['POST'])
def admin_draw():
    auth_info = request.authorization
    if not auth_info or not check_admin_auth(auth_info.username, auth_info.password):
        return authenticate()

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id FROM participants")
    participants = [row[0] for row in cur.fetchall()]

    if len(participants) < 25:
        conn.close()
        return "参加者が25名未満のため抽選できません。(当選20名 + 補欠5名)", 400

    selected = random.sample(participants, 25)
    winners = selected[:20]
    substitutes = selected[20:]

    cur.execute("DELETE FROM lottery_results")
    for w in winners:
        cur.execute("INSERT INTO lottery_results (participant_id, role) VALUES (?, 'winner')", (w,))
    for s in substitutes:
        cur.execute("INSERT INTO lottery_results (participant_id, role) VALUES (?, 'substitute')", (s,))

    conn.commit()
    conn.close()
    return "抽選が完了しました。<a href='/admin'>管理画面へ戻る</a>"

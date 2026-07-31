# -*- coding: utf-8 -*-
import random
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# --- 設定 ---
# 当選確率 (例: 0.20 = 20%の確率で当たる)
WIN_RATE = 0.20 

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>虹の原BRT 即時抽選</title>
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
        .header-nav {
            display: flex; justify-content: space-between; align-items: center;
            padding: 15px 30px; background: rgba(15, 23, 42, 0.8);
        }
        .container { max-width: 500px; margin: 40px auto; padding: 0 20px; }
        .glass-card {
            background: var(--card-bg); backdrop-filter: blur(12px);
            border: 1px solid var(--border-color); border-radius: 16px; padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37); text-align: center;
        }
        .btn {
            display: block; width: 100%; padding: 14px; background-color: var(--accent-color);
            color: white; border: none; border-radius: 8px; font-size: 1.1rem; font-weight: bold;
            cursor: pointer; transition: 0.3s; margin-top: 20px;
        }
        .btn:hover { background-color: #4f46e5; }
        .input-group { margin-bottom: 20px; text-align: left; }
        .input-group label { display: block; margin-bottom: 8px; color: var(--text-muted); }
        .input-control {
            width: 100%; padding: 12px; background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color); border-radius: 8px; color: white; box-sizing: border-box;
        }
        .result-box { margin-top: 25px; padding: 20px; border-radius: 12px; display: none; }
        .win { background: rgba(16, 185, 129, 0.2); border: 1px solid #10B981; color: #34D399; }
        .lose { background: rgba(239, 68, 68, 0.2); border: 1px solid #EF4444; color: #FCA5A5; }
        .notice-dm {
            margin-top: 15px; padding: 10px; background: rgba(255, 255, 255, 0.1);
            border-radius: 8px; font-weight: bold; color: #fff; font-size: 0.95rem;
        }
    </style>
</head>
<body>

    <header class="header-nav">
        <div style="font-weight:bold;"><i class="fa-solid fa-bus"></i> 虹の原BRT 即時抽選</div>
    </header>

    <div class="container">
        <div class="glass-card">
            <h2><i class="fa-solid fa-gift"></i> スピード抽選</h2>
            <p style="color: var(--text-muted); font-size: 0.9rem;">
                Robloxネームを入力して、抽選ボタンを押してください！
            </p>

            <form id="drawForm">
                <div class="input-group">
                    <label for="roblox_name">Roblox ネーム <span style="color:red">*</span></label>
                    <input type="text" id="roblox_name" class="input-control" placeholder="ユーザー名を入力" required>
                </div>
                <button type="submit" class="btn" id="drawBtn">今すぐ抽選する！</button>
            </form>

            <div id="resultBox" class="result-box">
                <h3 id="resultTitle" style="margin: 0 0 10px 0;"></h3>
                <p id="resultText" style="margin: 0;"></p>
                <div id="dmNotice" class="notice-dm" style="display: none;">
                    📸 当選された方は、この画面をスクリーンショット（スクショ）して <strong>@かいと</strong> のDMまでお送りください！
                </div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('drawForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('drawBtn');
            const resultBox = document.getElementById('resultBox');
            const dmNotice = document.getElementById('dmNotice');
            const name = document.getElementById('roblox_name').value;

            btn.disabled = true;
            btn.innerText = '抽選中...';

            const res = await fetch('/api/draw', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ roblox_name: name })
            });

            const data = await res.json();
            
            btn.style.display = 'none';
            document.getElementById('roblox_name').disabled = true;

            resultBox.style.display = 'block';
            if (data.is_win) {
                resultBox.className = 'result-box win';
                document.getElementById('resultTitle').innerText = '🎉 おめでとうございます！';
                document.getElementById('resultText').innerText = `${data.name} 様、当選しました！`;
                dmNotice.style.display = 'block'; // 当選時のみDM指示を表示
            } else {
                resultBox.className = 'result-box lose';
                document.getElementById('resultTitle').innerText = '😭 残念...';
                document.getElementById('resultText').innerText = `${data.name} 様、今回は落選となりました。`;
                dmNotice.style.display = 'none';
            }
        });
    </script>
</body>
</html>
"""

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/draw', methods=['POST'])
def draw():
    data = request.get_json()
    name = data.get('roblox_name', 'ゲスト').strip()

    # 確率判定
    is_win = random.random() < WIN_RATE

    return jsonify({
        'name': name,
        'is_win': is_win
    })

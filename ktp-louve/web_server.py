from flask import Flask, render_template_string, jsonify
import json
import os

app = Flask(__name__)

STATUS_FILE = "status.json"
OBJECT_NAME = "bottle"  # Should match detection.py

def read_status():
    """Read status from JSON file"""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r') as f:
                return json.load(f)
        else:
            return {
                "object_present": False,
                "last_seen": None,
                "movement_detected": False,
                "last_movement": None,
                "status_message": "Waiting for detection script..."
            }
    except Exception as e:
        return {
            "object_present": False,
            "last_seen": None,
            "movement_detected": False,
            "last_movement": None,
            "status_message": f"Error reading status: {e}"
        }

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Object Monitor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .status-card {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            border-left: 5px solid #667eea;
            transition: all 0.3s ease;
        }
        .status-card.present {
            border-left-color: #28a745;
            background: #d4edda;
        }
        .status-card.missing {
            border-left-color: #dc3545;
            background: #f8d7da;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }
        .status-icon {
            font-size: 48px;
            text-align: center;
            margin-bottom: 15px;
        }
        .status-text {
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 10px;
        }
        .timestamp {
            text-align: center;
            color: #666;
            font-size: 14px;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #ddd;
        }
        .info-row:last-child {
            border-bottom: none;
        }
        .label {
            font-weight: bold;
            color: #555;
        }
        .value {
            color: #333;
        }
        .connection-status {
            text-align: center;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .connection-status.connected {
            background: #d4edda;
            color: #155724;
        }
        .connection-status.disconnected {
            background: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Object Monitor</h1>
        <div id="connectionStatus" class="connection-status disconnected">
            ⚠️ Waiting for detection script...
        </div>
        <div id="statusCard" class="status-card">
            <div class="status-icon" id="statusIcon">⏳</div>
            <div class="status-text" id="statusText">Checking...</div>
            <div class="timestamp" id="timestamp">--</div>
        </div>
        <div class="status-card">
            <div class="info-row">
                <span class="label">Object:</span>
                <span class="value">{{ object_name }}</span>
            </div>
            <div class="info-row">
                <span class="label">Last Seen:</span>
                <span class="value" id="lastSeen">Never</span>
            </div>
            <div class="info-row">
                <span class="label">Last Movement:</span>
                <span class="value" id="lastMovement">None</span>
            </div>
        </div>
    </div>
    <script>
        let lastUpdate = null;
        
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    const card = document.getElementById('statusCard');
                    const icon = document.getElementById('statusIcon');
                    const text = document.getElementById('statusText');
                    const timestamp = document.getElementById('timestamp');
                    const connStatus = document.getElementById('connectionStatus');
                    
                    // Check if detection script is running
                    const now = Date.now();
                    if (lastUpdate && (now - lastUpdate) > 5000) {
                        connStatus.className = 'connection-status disconnected';
                        connStatus.textContent = '⚠️ Detection script not responding';
                    } else {
                        connStatus.className = 'connection-status connected';
                        connStatus.textContent = '✓ Connected to detection script';
                    }
                    lastUpdate = now;
                    
                    if (data.object_present) {
                        card.className = 'status-card present';
                        icon.textContent = '✅';
                        text.textContent = 'Object Present';
                        text.style.color = '#28a745';
                    } else {
                        card.className = 'status-card missing';
                        icon.textContent = '⚠️';
                        text.textContent = '🚨 OBJECT MISSING!';
                        text.style.color = '#dc3545';
                    }
                    
                    timestamp.textContent = data.status_message;
                    document.getElementById('lastSeen').textContent = data.last_seen || 'Never';
                    document.getElementById('lastMovement').textContent = data.last_movement || 'None';
                })
                .catch(error => {
                    console.error('Error fetching status:', error);
                    const connStatus = document.getElementById('connectionStatus');
                    connStatus.className = 'connection-status disconnected';
                    connStatus.textContent = '❌ Connection error';
                });
        }
        
        // Update every 500ms
        setInterval(updateStatus, 500);
        updateStatus();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, object_name=OBJECT_NAME.capitalize())

@app.route('/api/status')
def get_status():
    return jsonify(read_status())

if __name__ == "__main__":
    print("🌐 Starting web server...")
    print("📱 Open http://localhost:5000 in your browser")
    print("💡 Make sure detection.py is running in another terminal!")
    app.run(host='0.0.0.0', port=5000, debug=False)
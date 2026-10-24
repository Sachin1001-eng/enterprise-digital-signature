from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization
from flask import Flask, render_template_string, request, send_file
import io
import hashlib
import qrcode
import base64
from datetime import datetime

app = Flask(__name__)

# Generate RSA Key Pair globally
private_key = rsa.generate_private_key(
    public_exponent=65537, 
    key_size=2048
)
public_key = private_key.public_key()

stored_signature = None
original_data = b"Confidential Document: Q3 Project Financial Audit Report 2026."
backend_logs = []
audit_history = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Enterprise Digital Signature Dashboard</title>
    <style>
        :root {
            --primary-color: #0ea5e9; /* Vibrant Sky Blue */
            --success-color: #22c55e; /* Vibrant Emerald Green */
            --danger-color: #ef4444;  /* Vibrant Red */
            --warning-color: #f59e0b; /* Vibrant Amber */
            --bg-dark: #0f172a;       /* Deep Navy */
            --card-bg: rgba(30, 41, 59, 0.7);
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --border-color: rgba(148, 163, 184, 0.2);
        }

        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #0f172a, #1e293b); color: var(--text-main); margin: 0; padding: 20px; min-height: 100vh; }
        .container { max-width: 1100px; margin: auto; background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(15px); padding: 35px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.6); border: 1px solid var(--border-color); }
        h1 { text-align: center; color: var(--primary-color); margin-bottom: 5px; font-size: 28px; letter-spacing: 1.5px; text-transform: uppercase; }
        .subtitle { text-align: center; color: var(--text-muted); margin-bottom: 25px; font-size: 14px; font-style: italic; }
        .status-bar { background: rgba(30, 41, 59, 0.5); padding: 12px 20px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; border: 1px solid var(--border-color); margin-bottom: 25px; }
        .grid { display: flex; gap: 25px; flex-wrap: wrap; }
        .card { flex: 1; min-width: 460px; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 14px; padding: 28px; box-shadow: 0 6px 20px rgba(0,0,0,0.4); }
        .card h3 { margin-top: 0; color: var(--primary-color); font-size: 20px; border-bottom: 2px solid var(--primary-color); padding-bottom: 12px; margin-bottom: 20px;}
        label { display: block; margin-top: 18px; font-weight: bold; font-size: 14px; color: var(--text-main); }
        textarea, input[type="file"] { width: 100%; padding: 14px; margin-top: 8px; background: #020617; border: 2px solid #334155; border-radius: 10px; color: var(--text-main); font-family: monospace; font-size: 14px; box-sizing: border-box; transition: all 0.3s; }
        textarea:focus, input[type="file"]:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 12px rgba(14, 165, 233, 0.4); }
        textarea { height: 100px; resize: vertical; }
        button { width: 100%; margin-top: 22px; padding: 14px; background: linear-gradient(135deg, var(--primary-color), #0284c7); color: white; border: none; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.4s ease; text-transform: uppercase; letter-spacing: 1px; }
        button:hover { background: linear-gradient(135deg, #0284c7, #0ea5e9); box-shadow: 0 6px 18px rgba(14, 165, 233, 0.5); transform: translateY(-2px); }
        .btn-verify { background: linear-gradient(135deg, var(--success-color), #15803d); }
        .btn-verify:hover { background: linear-gradient(135deg, #15803d, #22c55e); box-shadow: 0 6px 18px rgba(34, 197, 94, 0.5); }
        .btn-download { background: #475569; margin-top: 8px; padding: 12px; font-size: 14px; text-decoration: none; display: block; text-align: center; color: var(--text-main); border-radius: 10px; border: 1px solid #64748b; transition: all 0.3s; }
        .btn-download:hover { background: #64748b; color: #fff; transform: scale(1.02); }
        .sig-box, .log-box { margin-top: 12px; background: #020617; color: var(--success-color); padding: 14px; border-radius: 10px; font-family: monospace; font-size: 12px; word-break: break-all; max-height: 110px; overflow-y: auto; border: 2px solid #334155; }
        .log-box { color: var(--text-muted); }
        .alert { margin-top: 18px; padding: 14px; border-radius: 10px; font-weight: bold; text-align: center; font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px; }
        .alert-success { background-color: rgba(34, 197, 94, 0.2); color: var(--success-color); border: 2px solid var(--success-color); }
        .alert-danger { background-color: rgba(239, 68, 68, 0.2); color: var(--danger-color); border: 2px solid var(--danger-color); }
        .alert-warning { background-color: rgba(245, 158, 11, 0.2); color: var(--warning-color); border: 2px solid var(--warning-color); }
        .badge-sec { background: #334155; padding: 5px 12px; border-radius: 8px; font-size: 12px; color: var(--primary-color); font-family: monospace; border: 1px solid #475569; margin-left: 5px; }
        .key-row { display: flex; gap: 15px; margin-top: 20px; }
        .qr-container { text-align: center; margin-top: 18px; background: rgba(15, 23, 42, 0.6); padding: 14px; border-radius: 10px; border: 2px dashed #475569; }
        table { width: 100%; border-collapse: separate; border-spacing: 0 8px; margin-top: 15px; font-size: 13px; color: var(--text-main); }
        th, td { border: none; padding: 12px; text-align: left; background: rgba(30, 41, 59, 0.4); }
        th { background: #020617; color: var(--primary-color); text-transform: uppercase; font-size: 11px; letter-spacing: 1px; }
        tr:first-child th:first-child { border-radius: 10px 0 0 10px; }
        tr:first-child th:last-child { border-radius: 0 10px 10px 0; }
        td:first-child { border-radius: 10px 0 0 10px; }
        td:last-child { border-radius: 0 10px 10px 0; }
        tr { transition: all 0.2s; }
        tr:hover td { background: rgba(30, 41, 59, 0.7); }
        .action-sign { color: var(--primary-color); font-weight: bold; }
        .action-verify { color: var(--success-color); font-weight: bold; }
        .status-icon { font-size: 1.2em; vertical-align: middle; margin-right: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Enterprise Digital Signature Dashboard</h1>
        <div class="subtitle">Secure Cryptographic Suite powered by RSA-2048 & SHA-256 PSS</div>

        <div class="status-bar">
            <div><strong>System Status:</strong> <span style="color: var(--success-color);"><span class="status-icon">●</span>Online & Secured</span></div>
            <div>
                <span class="badge-sec">RSA-2048</span> 
                <span class="badge-sec">SHA-256 PSS</span>
                <span class="badge-sec">QR & Audit</span>
            </div>
        </div>

        <div class="key-row">
            <a href="/download/private" class="btn-download">📥 Download Private Key (.pem)</a>
            <a href="/download/public" class="btn-download">📥 Download Public Key (.pem)</a>
        </div>

        <div class="grid" style="margin-top: 25px;">
            <!-- Sign Card -->
            <div class="card" style="border-top: 6px solid var(--primary-color);">
                <h3>Step 1: Document Signing (Sender)</h3>
                <form method="POST" action="/sign" enctype="multipart/form-data">
                    <label>Upload Document / File:</label>
                    <input type="file" name="file">
                    
                    <label>Or Enter Raw Text Content:</label>
                    <textarea name="message">{{ message }}</textarea>
                    
                    <button type="submit">Generate Signature & QR Code</button>
                </form>
                {% if signature %}
                    <label style="color: var(--success-color); margin-top: 15px;">Generated Signature (Hex):</label>
                    <div class="sig-box">{{ signature }}</div>
                    
                    {% if qr_code %}
                        <div class="qr-container">
                            <label style="color: var(--text-main); margin-bottom: 8px;">📱 Signature Verification QR Code:</label>
                            <img src="data:image/png;base64,{{ qr_code }}" alt="Signature QR Code" width="140" style="border-radius: 6px; border: 4px solid #fff;">
                        </div>
                    {% endif %}
                    
                    <a href="/download/sig" class="btn-download" style="background: #db2777; color: white; margin-top: 15px; border: none;">📥 Download Signature File (.sig)</a>
                {% endif %}
            </div>

            <!-- Verify Card -->
            <div class="card" style="border-top: 6px solid var(--success-color);">
                <h3>Step 2: Verification & Tamper Detection</h3>
                <form method="POST" action="/verify" enctype="multipart/form-data">
                    <label>Review or Modify Content to Test Tampering:</label>
                    <textarea name="verify_message">{{ verify_message }}</textarea>
                    
                    <label>Upload Signature File (.sig) (Optional):</label>
                    <input type="file" name="sig_file">
                    
                    <button type="submit" class="btn-verify">Verify Signature Integrity</button>
                </form>
                {% if result %}
                    <div class="alert {% if is_valid %}alert-success{% elif is_valid == False %}alert-danger{% else %}alert-warning{% endif %}">
                        {% if is_valid %}<span class="status-icon">✅</span>{% elif is_valid == False %}<span class="status-icon">❌</span>{% else %}<span class="status-icon">⚠️</span>{% endif %}
                        {{ result }}
                    </div>
                {% endif %}
            </div>
        </div>

        <!-- Audit History Table -->
        <div style="margin-top: 30px;">
            <h3 style="color: var(--text-main); font-size: 18px; border-bottom: 2px solid #334155; padding-bottom: 8px;">📋 Database Audit Trail (Transaction History)</h3>
            <div style="max-height: 180px; overflow-y: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Action Type</th>
                            <th>Details / Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% if history %}
                            {% for item in history %}
                                <tr>
                                    <td style="color: var(--text-muted);">{{ item.time }}</td>
                                    <td><strong class="{% if item.action == 'SIGN' %}action-sign{% else %}action-verify{% endif %}">{{ item.action }}</strong></td>
                                    <td>{{ item.detail }}</td>
                                </tr>
                            {% endfor %}
                        {% else %}
                            <tr><td colspan="3" style="text-align: center; color: var(--text-muted);">No transactions recorded yet.</td></tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Backend Log Section -->
        <div style="margin-top: 30px;">
            <h3 style="color: var(--text-main); font-size: 18px; border-bottom: 2px solid #334155; padding-bottom: 8px;">🖥️ Live Backend Cryptographic Trace</h3>
            <div class="log-box">
                {% if logs %}
                    {% for log in logs %}
                        <div>{{ log }}</div>
                    {% endfor %}
                {% else %}
                    <div>[System Ready] Waiting for signature or verification action...</div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
"""

def generate_qr(data_str):
    qr = qrcode.QRCode(version=1, box_size=6, border=3)
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="white", back_color="#020617")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

@app.route('/')
def home():
    global original_data, backend_logs, audit_history
    msg_str = original_data.decode('utf-8', errors='ignore')
    return render_template_string(HTML_TEMPLATE, message=msg_str, verify_message=msg_str, logs=backend_logs, history=audit_history)

@app.route('/sign', methods=['POST'])
def sign():
    global stored_signature, original_data, backend_logs, audit_history
    backend_logs.clear()
    
    uploaded_file = request.files.get('file')
    if uploaded_file and uploaded_file.filename != '':
        original_data = uploaded_file.read()
        msg_str = f"[Uploaded File: {uploaded_file.filename}]"
        backend_logs.append(f"[+] File received: {uploaded_file.filename} ({len(original_data)} bytes)")
    else:
        msg_str = request.form.get('message', '')
        original_data = msg_str.encode('utf-8')
        backend_logs.append(f"[+] Raw text received: '{msg_str}' ({len(original_data)} bytes)")

    digest = hashlib.sha256(original_data).hexdigest()
    backend_logs.append(f"[*] Step A: Computed SHA-256 Message Digest -> {digest[:32]}...")

    backend_logs.append(f"[*] Step B: Applying RSA-2048 Private Key with PSS padding...")
    stored_signature = private_key.sign(
        original_data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    backend_logs.append(f"[+] Success: Digital signature successfully generated.")

    qr_b64 = generate_qr(stored_signature.hex()[:40])

    audit_history.insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": "SIGN",
        "detail": f"Document signed successfully (Hash: {digest[:8]}...)"
    })

    return render_template_string(HTML_TEMPLATE, message=msg_str, verify_message=msg_str, signature=stored_signature.hex(), qr_code=qr_b64, logs=backend_logs, history=audit_history)

@app.route('/verify', methods=['POST'])
def verify():
    global stored_signature, original_data, backend_logs, audit_history
    backend_logs.clear()
    
    verify_msg = request.form.get('verify_message', '')
    sig_file = request.files.get('sig_file')
    
    sig_to_verify = stored_signature
    if sig_file and sig_file.filename != '':
        sig_to_verify = sig_file.read()
        backend_logs.append(f"[+] Uploaded .sig file loaded for verification.")

    if sig_to_verify is None:
        backend_logs.append(f"[-] Error: No signature found to verify.")
        return render_template_string(HTML_TEMPLATE, message=verify_msg, verify_message=verify_msg, result="⚠️ Please generate or upload a signature first!", is_valid=None, logs=backend_logs, history=audit_history)

    data_to_verify = verify_msg.encode('utf-8')
    current_digest = hashlib.sha256(data_to_verify).hexdigest()
    backend_logs.append(f"[*] Step 1: Recalculating SHA-256 hash -> {current_digest[:32]}...")
    backend_logs.append(f"[*] Step 2: Running Public Key verification check...")

    try:
        public_key.verify(
            sig_to_verify,
            data_to_verify,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        backend_logs.append(f"[+] Step 3: Hash matches! Signature mathematically valid.")
        result = "✅ SUCCESS: Signature is VALID! The document/file is authentic, intact, and unmodified."
        is_valid = True
        
        audit_history.insert(0, {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": "VERIFY",
            "detail": "Success - Signature Valid & Unmodified"
        })
    except InvalidSignature:
        backend_logs.append(f"[-] Step 3 FAILED: Hash mismatch or signature tampered!")
        result = "❌ ALERT: TAMPERING DETECTED! Unauthorized modification or invalid signature detected."
        is_valid = False
        
        audit_history.insert(0, {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": "VERIFY",
            "detail": "Alert - Tampering Detected / Invalid Signature"
        })

    qr_b64 = generate_qr(sig_to_verify.hex()[:40]) if isinstance(sig_to_verify, bytes) else None

    return render_template_string(HTML_TEMPLATE, message=verify_msg, verify_message=verify_msg, signature=sig_to_verify.hex() if isinstance(sig_to_verify, bytes) else None, qr_code=qr_b64, result=result, is_valid=is_valid, logs=backend_logs, history=audit_history)

@app.route('/download/private')
def download_private():
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    return send_file(io.BytesIO(pem), mimetype='application/x-pem-file', as_attachment=True, download_name='private_key.pem')

@app.route('/download/public')
def download_public():
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return send_file(io.BytesIO(pem), mimetype='application/x-pem-file', as_attachment=True, download_name='public_key.pem')

@app.route('/download/sig')
def download_sig():
    global stored_signature
    if stored_signature is None:
        return "No signature available to download.", 400
    return send_file(io.BytesIO(stored_signature), mimetype='application/octet-stream', as_attachment=True, download_name='document.sig')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
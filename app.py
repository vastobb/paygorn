import os
import random
import string
from flask import Flask, request, jsonify

app = Flask(__name__)

# ── 100% FREE CLOUD DATABASE (MANAGES ACTIVE LICENSE STRINGS & HWID LOCKS) ──
# Keys are added dynamically when users complete LootLabs tasks.
# Format: "RANDOMKEY123": {"uses": 0, "hwid": None}
KEYS_DATABASE = {}

def generate_pure_random_key(length=12):
    """Generates a 100% random uppercase alphanumeric key string with no prefix."""
    chars = string.ascii_uppercase + string.digits
    while True:
        new_key = "".join(random.choice(chars) for _ in range(length))
        # Ensure it is genuinely unique and never duplicated
        if new_key not in KEYS_DATABASE:
            return new_key

@app.route('/get-key', methods=['GET'])
def get_key():
    """
    1. LootLabs redirects a user here upon completing tasks.
    2. This creates ONE fresh, totally random key on the spot.
    3. It displays ONLY that 1 key to that 1 specific person.
    """
    single_key = generate_pure_random_key(length=12)
    
    # Register the fresh key into your active database with 0 initial uses
    KEYS_DATABASE[single_key] = {"uses": 0, "hwid": None}
    
    return f"""
    <html>
        <head><title>Access Key Claimed</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 100px; background-color: #121212; color: #ffffff;">
            <h2 style="color: #aaaaaa;">Task Complete! Your Unique Key is:</h2>
            <h1 style="color: #00ffcc; background: #222; padding: 15px 30px; display: inline-block; border-radius: 6px; border: 1px solid #333; font-vars: monospace; letter-spacing: 3px;">{single_key}</h1>
            <p style="color: #777777; margin-top: 20px;">This key is valid for 10 video renders and is locked to your device HWID.</p>
        </body>
    </html>
    """

@app.route('/check-key-status', methods=['POST'])
def check_key_status():
    """Verifies that the key exists, has tokens left, and matches the user's HWID."""
    data = request.json or {}
    user_key = data.get("key")
    user_hwid = data.get("hwid")
    
    if user_key in KEYS_DATABASE:
        key_data = KEYS_DATABASE[user_key]
        if key_data["uses"] >= 10:
            return jsonify({"valid": False, "message": "Key out of tokens."})
        if key_data["hwid"] is not None and key_data["hwid"] != user_hwid:
            return jsonify({"valid": False, "message": "HWID lock error: This key belongs to another device."})
        return jsonify({"valid": True, "uses_left": 10 - key_data["uses"]})
        
    return jsonify({"valid": False, "message": "Invalid or non-existent key."})

@app.route('/validate-script-key', methods=['POST'])
def validate_key():
    """Deducts exactly 1 use token and binds the device HWID on first render profile activity."""
    data = request.json or {}
    user_key = data.get("key")
    user_hwid = data.get("hwid")

    if user_key in KEYS_DATABASE:
        key_data = KEYS_DATABASE[user_key]
        if key_data["uses"] >= 10:
            return jsonify({"valid": False, "message": "Key expired."})
        if key_data["hwid"] is not None and key_data["hwid"] != user_hwid:
            return jsonify({"valid": False, "message": "HWID mismatch profile."})
            
        # Lock to device hardware footprint permanently on its first video run
        if key_data["hwid"] is None:
            key_data["hwid"] = user_hwid
            
        key_data["uses"] += 1  # Subtract 1 token
        return jsonify({"valid": True, "uses_left": 10 - key_data["uses"]})
        
    return jsonify({"valid": False, "message": "Authentication core mismatch structure."})

if __name__ == '__main__':
    # Default port configuration for cloud host matching platforms
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


from flask import Flask, request, jsonify
from flask_cors import CORS
import herbie_datagrab
import traceback
import os
import requests
from datetime import datetime

app = Flask(__name__)

# FIXED: More permissive CORS configuration
CORS(app, 
     resources={r"/api/*": {"origins": "*"}},  # Allow all origins for API endpoints
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS"])

# Load eBird API key from environment variable
EBIRD_API_KEY = os.getenv('EBIRD_API_KEY')
if not EBIRD_API_KEY:
    print("WARNING: EBIRD_API_KEY environment variable not set!")

# eBird API base URL
EBIRD_BASE_URL = "https://api.ebird.org/v2"

@app.after_request
def after_request(response):
    """Add CORS headers to every response"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route("/api/get_gfs_data", methods=["POST", "OPTIONS"])
def get_gfs_data():
    if request.method == 'OPTIONS':
        # CORS preflight response
        return jsonify({'status': 'ok'}), 200

    # Handle actual POST
    data = request.get_json()
    lat = data.get('lat')
    lon = data.get('lon')
    date = data.get('date')
    level = data.get('level', 850)

    try:
        result = herbie_datagrab.process_wind_data(lat, lon, date, level)
        if result is not None:
            return jsonify({"status": "success", "message": result})
        else:
            return jsonify({"status": "error", "message": "Failed to fetch GFS data"}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# Weather data endpoint specifically for external weather site
@app.route("/api/weather", methods=["GET", "OPTIONS"])
def get_weather_for_location():
    """Get weather data for a specific location and time - for external website"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    datetime_str = request.args.get('datetime')
    level = request.args.get('level', default=850, type=int)
    
    print(f"Weather API request: lat={lat}, lng={lng}, datetime={datetime_str}, level={level}")
    
    if not all([lat, lng, datetime_str]):
        return jsonify({"error": "Missing required parameters: lat, lng, datetime"}), 400
    
    try:
        result = herbie_datagrab.process_wind_data(lat, lng, datetime_str, level)
        if result is not None:
            return jsonify({
                "status": "success", 
                "data": result,
                "metadata": {
                    "lat": lat,
                    "lng": lng,
                    "datetime": datetime_str,
                    "level": level,
                    "processed_at": datetime.now().isoformat()
                }
            })
        else:
            return jsonify({"status": "error", "message": "Failed to fetch weather data"}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# Health check endpoint
@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ebird_api_configured": EBIRD_API_KEY is not None,
        "services": ["gfs_data", "weather_api"],
        "cors_enabled": True
    })

if __name__ == '__main__':
    # Print startup info
    print("🚀 Starting Enhanced Herbie Server...")
    print(f"📡 eBird API Key: {'✅ Configured' if EBIRD_API_KEY else '❌ Missing'}")
    print(f"🌤️  Weather Data: ✅ Available")
    print(f"🔗 CORS: ✅ Enabled for ALL origins (*)")
    print("\n📍 Registered Endpoints:")
    for rule in app.url_map.iter_rules():
        print(f"   - {rule.methods} {rule.rule}")
    print("\n⚠️  Server running on localhost:8000 - accessible only from this machine")
    print("💡 For production deployment, update CORS settings to specific domains\n")
    print("✅ Server starting on http://0.0.0.0:8000")
    print("✅ Test with: curl http://localhost:8000/api/health\n")
    
    app.run(debug=True, host="0.0.0.0", port=8000, threaded=True)
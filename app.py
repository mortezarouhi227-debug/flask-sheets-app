import os
import traceback
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello 👋 Flask app is running on Render/Cloud Run!"

@app.route("/run-performance-segments")
def run_performance_segments():
    try:
        import Performance_Segments
        msg = Performance_Segments.main()
        return f"✅ Performance segments executed successfully: {msg}"
    except Exception as e:
        error_text = f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
        print(error_text)  # در لاگ سرویس هم ذخیره میشه
        return error_text, 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

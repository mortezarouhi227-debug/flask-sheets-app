from flask import Flask
import Performance_Segments  # ایمپورت فایل Performance_Segments.py

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Flask on Render! 🎉"

@app.route("/performance_segments")
def run_performance_segments():
    try:
        result = Performance_Segments.main()
        return f"✅ Done: {result}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

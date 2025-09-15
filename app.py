from flask import Flask
import Performance_Segments  # ایمپورت کد پردازش

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Flask on Render! 🎉"

@app.route("/run")
def run_performance_segments():
    try:
        msg = Performance_Segments.main()
        return f"✅ Done: {msg}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

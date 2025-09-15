from flask import Flask
import Performance_Segments  # همون فایلی که بالا نوشتی

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Flask on Render! 🎉"

@app.route("/update")
def update_segments():
    msg = Performance_Segments.main()
    return msg

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

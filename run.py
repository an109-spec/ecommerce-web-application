import os 
from dotenv import load_dotenv
from app.extensions.socketio import socketio
load_dotenv()
from app import create_app
app = create_app()


if __name__ == "__main__":
    port_env = int(os.environ.get("PORT", 5000))
    print(f"--- 🚀 Ứng dụng đang khởi chạy trên port: {port_env} ---")
    socketio.run(
        app,
        host="0.0.0.0",
        port=port_env,
        allow_unsafe_werkzeug=True
    )



import os
import eventlet
eventlet.monkey_patch()

from app import create_app
from app.extensions import socketio

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080, debug=True)

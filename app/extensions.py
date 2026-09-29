from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS

db       = SQLAlchemy()
migrate  = Migrate()
jwt      = JWTManager()
bcrypt   = Bcrypt()
cors     = CORS()
from flask_socketio import SocketIO
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")

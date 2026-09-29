import os
from flask import Flask
from app.extensions import db, migrate, jwt, bcrypt, cors, socketio
from config import config


def create_app(env="development"):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"),
    )
    app.config.from_object(config[env])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    socketio.init_app(app)

    from app.api.auth.routes         import auth_bp
    from app.api.profile.routes      import profile_bp
    from app.api.jobs.routes         import jobs_bp
    from app.api.recommendations.routes import rec_bp
    from app.api.skill_gap.routes    import skill_gap_bp
    from app.api.applications.routes import applications_bp
    from app.api.saved_jobs.routes   import saved_jobs_bp
    from app.api.feed.routes         import feed_bp
    from app.api.connections.routes  import connections_bp
    from app.api.messages.routes     import messages_bp
    from app.api.recruiter.routes    import recruiter_bp
    from app.api.notifications.routes import notif_bp
    from app.views                   import views_bp

    app.register_blueprint(auth_bp,         url_prefix="/api/auth")
    app.register_blueprint(profile_bp,      url_prefix="/api/profile")
    app.register_blueprint(jobs_bp,         url_prefix="/api/jobs")
    app.register_blueprint(rec_bp,          url_prefix="/api/recommendations")
    app.register_blueprint(skill_gap_bp,    url_prefix="/api/skill-gap")
    app.register_blueprint(applications_bp, url_prefix="/api/applications")
    app.register_blueprint(saved_jobs_bp,   url_prefix="/api/saved-jobs")
    app.register_blueprint(feed_bp,         url_prefix="/api/feed")
    app.register_blueprint(connections_bp,  url_prefix="/api/connections")
    app.register_blueprint(messages_bp,     url_prefix="/api/messages")
    app.register_blueprint(recruiter_bp,    url_prefix="/api/recruiter")
    app.register_blueprint(notif_bp,        url_prefix="/api/notifications")
    app.register_blueprint(views_bp)

    # Register SocketIO events
    from app.sockets import register_events
    register_events(socketio)

    with app.app_context():
        db.create_all()

    return app

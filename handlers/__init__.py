def setup_handlers(app):
    from .user import register_user_handlers
    register_user_handlers(app)

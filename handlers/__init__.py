from .user import register_user_handlers
from .admin import register_admin_handlers

def setup_handlers(app):
    register_user_handlers(app)
    register_admin_handlers(app)

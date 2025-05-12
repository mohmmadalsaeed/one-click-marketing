import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
from src.models.user import db # Assuming db is initialized elsewhere or will be initialized if DB is used
from src.routes.auth import auth_bp
from src.routes.admin import admin_bp
from src.routes.meta_integration import meta_integration_bp
from src.routes.messaging import messaging_bp
from src.routes.templates import templates_bp
from src.routes.campaigns import campaigns_bp
from src.routes.reports import reports_bp
from src.routes.admin_pricing import admin_pricing_bp
from src.routes.client_portal import client_portal_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_default_secret_key_please_change_in_prod')

# Register blueprints
# All blueprints should ideally have their own url_prefix defined within them if they are to be nested under /api
# Or, ensure the Vercel rewrite handles the /api prefix correctly and blueprints are defined from root of that /api path.
# The current user_bp was registered with url_prefix='/api' in the original main.py.
# For Vercel, if vercel.json rewrites /api/(.*) to the app, then blueprints should be registered without /api prefix here,
# or if they have /api, it would become /api/api. Let's assume blueprints are defined from the root of the app,
# and /api is handled by Vercel rewrite + blueprint prefix.

# Example from original code: app.register_blueprint(user_bp, url_prefix='/api')
# If user_bp itself has routes like @user_bp.route('/login'), it becomes /api/login.
# If user_bp has routes like @user_bp.route('/api/login'), it becomes /api/api/login. This is likely wrong.
# Let's assume the blueprints (auth_bp, admin_bp etc.) are defined with their specific paths (e.g. /auth, /admin/users)
# and they will be accessible under /api/auth, /api/admin/users etc. due to the Vercel rewrite and how Flask handles blueprints.

# Re-registering all blueprints found in the project, assuming they are structured to be prefixed by /api via Vercel's rewrite
# The individual blueprint files should define their routes relative to their registration point.
# For example, in auth.py: @auth_bp.route('/login') will become /api/auth/login if auth_bp is registered with url_prefix='/auth'
# and the main app is hit via /api by Vercel.

app.register_blueprint(auth_bp, url_prefix='/auth') # Will be /api/auth
app.register_blueprint(admin_bp, url_prefix='/admin') # Will be /api/admin
app.register_blueprint(meta_integration_bp, url_prefix='/meta') # Will be /api/meta
app.register_blueprint(messaging_bp, url_prefix='/messaging') # Will be /api/messaging
app.register_blueprint(templates_bp, url_prefix='/templates') # Will be /api/templates
app.register_blueprint(campaigns_bp, url_prefix='/campaigns') # Will be /api/campaigns
app.register_blueprint(reports_bp, url_prefix='/reports') # Will be /api/reports
app.register_blueprint(admin_pricing_bp, url_prefix='/admin-pricing') # Will be /api/admin-pricing
app.register_blueprint(client_portal_bp, url_prefix='/client-portal') # Will be /api/client-portal


# Database Configuration (User must set these environment variables in Vercel)
if os.getenv('DB_HOST'): # Only configure DB if DB_HOST is set
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    # It's generally not recommended to run db.create_all() on every app start in production.
    # Migrations should be handled separately. For a simple setup or initial deployment, it might be okay.
    # Consider using Flask-Migrate or a similar tool for database migrations.
    # with app.app_context():
    #     db.create_all() # User might need to run this once or handle migrations

# The main Flask app instance is 'app', which Vercel will pick up.
# No need for app.run() as Vercel handles the serving.


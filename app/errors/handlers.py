from flask import Blueprint, render_template

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)
def error_404(error):
    # 404: Page Not Found
    # We return the template and the specific status code 404
    return render_template('errors/404.html', error = error), 404

@errors_bp.app_errorhandler(403)
def error_403(error):
    # 403: Forbidden (Access Denied)
    return render_template('errors/403.html', error=error), 403

@errors_bp.app_errorhandler(500)
def error_500(error):
    # 500: Internal Server Error (Crash)
    return render_template('errors/500.html', error=error), 500
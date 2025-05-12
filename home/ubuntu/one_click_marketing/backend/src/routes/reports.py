# backend/src/routes/reports.py

from flask import Blueprint, request, jsonify
from ..services.reporting_service import ReportingService
from ..routes.meta_integration import token_required # Re-use the token_required decorator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

reports_bp = Blueprint("reports_bp", __name__, url_prefix="/api/v1/reports")

@reports_bp.route("/financial-summary", methods=["GET"])
@token_required
def get_financial_summary_report():
    client_id = request.current_user_id
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    # Default to last 30 days if no dates provided
    if not end_date_str:
        end_date = datetime.utcnow()
    else:
        try:
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
        except ValueError:
            return jsonify({"message": "Invalid end_date format. Use ISO 8601."}), 400
    
    if not start_date_str:
        start_date = end_date - timedelta(days=30)
    else:
        try:
            start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
        except ValueError:
            return jsonify({"message": "Invalid start_date format. Use ISO 8601."}), 400

    if start_date > end_date:
        return jsonify({"message": "start_date cannot be after end_date."}), 400

    summary = ReportingService.get_financial_summary(client_id, start_date, end_date)
    if summary:
        return jsonify(summary), 200
    else:
        return jsonify({"message": "Could not generate financial summary."}), 500

@reports_bp.route("/campaign-performance", methods=["GET"])
@token_required
def get_campaign_performance_report():
    client_id = request.current_user_id
    campaign_id_str = request.args.get("campaign_id")
    campaign_id = None
    if campaign_id_str:
        try:
            campaign_id = int(campaign_id_str)
        except ValueError:
            return jsonify({"message": "Invalid campaign_id format. Must be an integer."}), 400

    summary = ReportingService.get_campaign_performance_summary(client_id, campaign_id)
    return jsonify(summary), 200

@reports_bp.route("/daily-transactions", methods=["GET"])
@token_required
def get_daily_transactions_report():
    client_id = request.current_user_id
    date_str = request.args.get("date") # Expects YYYY-MM-DD

    if not date_str:
        target_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

    summary = ReportingService.get_daily_transaction_summary(client_id, target_date)
    if summary:
        return jsonify(summary), 200
    else:
        return jsonify({"message": "Could not generate daily transaction summary."}), 500

# Remember to register this blueprint in your main Flask app (e.g., main.py)
# from .routes.reports import reports_bp
# app.register_blueprint(reports_bp)


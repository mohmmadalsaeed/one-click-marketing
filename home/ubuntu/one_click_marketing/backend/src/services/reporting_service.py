# backend/src/services/reporting_service.py

from sqlalchemy import func, case
from datetime import datetime, timedelta
from ..models.user import db, User, ClientProfile
from ..models.campaign import Campaign
from ..models.message_log import MessageLog, MessageStatus
from ..models.wallet_transaction import WalletTransaction, TransactionType
from ..models.client_pricing import ClientPricing # Import ClientPricing
import logging
import decimal

logger = logging.getLogger(__name__)

# Define a system default price per message if no client-specific price is found
SYSTEM_DEFAULT_PRICE_PER_MESSAGE = decimal.Decimal("0.0150") # Example: $0.0150
SYSTEM_DEFAULT_CURRENCY = "USD"

class ReportingService:

    @staticmethod
    def get_client_message_price(client_id: int) -> tuple[decimal.Decimal, str]:
        """Fetches the client-specific price per message or returns system default."""
        client_pricing = ClientPricing.query.filter_by(client_id=client_id).first()
        if client_pricing and client_pricing.price_per_message is not None:
            return client_pricing.price_per_message, client_pricing.currency
        # Fallback to a system-wide default price if no specific pricing is set
        # This default could also come from a configuration file or another model
        return SYSTEM_DEFAULT_PRICE_PER_MESSAGE, SYSTEM_DEFAULT_CURRENCY

    @staticmethod
    def record_transaction_and_update_balance(
        client_id: int, 
        amount: decimal.Decimal, 
        transaction_type: TransactionType, 
        description: str, 
        currency: str = None, # Currency can be passed or determined by client profile/pricing
        campaign_id: int = None, 
        message_log_id: int = None,
        reference_id: str = None
    ):
        """Records a wallet transaction and updates the client's wallet balance."""
        client_profile = ClientProfile.query.filter_by(user_id=client_id).first()
        if not client_profile:
            logger.error(f"Client profile not found for client_id: {client_id}")
            raise ValueError("Client profile not found")

        # Determine currency if not explicitly provided
        final_currency = currency or client_profile.currency or SYSTEM_DEFAULT_CURRENCY

        # For MESSAGE_COST, amount should be negative and based on pricing
        # The 'amount' parameter for this function should be the *cost* (positive value)
        # and we make it negative here for deduction.
        if transaction_type == TransactionType.MESSAGE_COST:
            # The 'amount' passed for MESSAGE_COST should be the actual cost (positive)
            # It will be stored as negative in the transaction.
            if amount <= decimal.Decimal("0"):
                 logger.warning(f"MESSAGE_COST transaction for client {client_id} has non-positive amount: {amount}. Assuming it's the cost to be deducted.")
            transaction_amount = -abs(amount) # Ensure it's a debit
        else:
            transaction_amount = decimal.Decimal(str(amount)) # Convert if not already decimal

        new_transaction = WalletTransaction(
            client_id=client_id,
            amount=transaction_amount, # Stored as negative for debits, positive for credits
            transaction_type=transaction_type,
            description=description,
            campaign_id=campaign_id,
            message_log_id=message_log_id,
            currency=final_currency,
            reference_id=reference_id
        )
        db.session.add(new_transaction)

        # Update wallet balance
        client_profile.wallet_balance += transaction_amount # transaction_amount is already signed
        db.session.add(client_profile)

        try:
            db.session.commit()
            logger.info(f"Transaction {new_transaction.id} recorded for client {client_id}. New balance: {client_profile.wallet_balance}")
            return new_transaction
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to record transaction for client {client_id}: {str(e)}", exc_info=True)
            raise

    # This function would be called, for example, after a message is successfully sent by whatsapp_service.py
    # It needs the message_log_id to link the cost to the specific message.
    @staticmethod
    def charge_for_message(client_id: int, message_log_id: int, campaign_id: int = None):
        """Charges a client for a sent message based on their pricing."""
        price_per_message, currency = ReportingService.get_client_message_price(client_id)
        
        # The price_per_message is the cost to be deducted.
        # The record_transaction_and_update_balance function expects a positive cost for MESSAGE_COST type,
        # and will make it negative internally for the transaction amount.
        cost_for_this_message = price_per_message 

        description = f"Cost for message ID {message_log_id}"
        if campaign_id:
            description += f" (Campaign ID {campaign_id})"
        
        try:
            ReportingService.record_transaction_and_update_balance(
                client_id=client_id,
                amount=cost_for_this_message, # Pass the positive cost
                transaction_type=TransactionType.MESSAGE_COST,
                description=description,
                currency=currency,
                message_log_id=message_log_id,
                campaign_id=campaign_id
            )
            logger.info(f"Successfully charged client {client_id} an amount of {cost_for_this_message} {currency} for message {message_log_id}.")
        except Exception as e:
            logger.error(f"Failed to charge client {client_id} for message {message_log_id}: {str(e)}", exc_info=True)
            # Handle failure to charge (e.g., log, notify admin, retry logic if applicable)
            # This is critical as it affects billing.

    @staticmethod
    def get_financial_summary(client_id: int, start_date: datetime, end_date: datetime):
        """Calculates financial summary for a client within a date range."""
        try:
            end_date_inclusive = end_date + timedelta(days=1) - timedelta(microseconds=1)

            total_top_ups = db.session.query(func.sum(WalletTransaction.amount)) \
                .filter(
                    WalletTransaction.client_id == client_id,
                    WalletTransaction.transaction_type == TransactionType.TOP_UP,
                    WalletTransaction.transaction_date >= start_date,
                    WalletTransaction.transaction_date <= end_date_inclusive
                ).scalar() or decimal.Decimal("0.00")

            total_deductions_query = db.session.query(func.sum(WalletTransaction.amount)) \
                .filter(
                    WalletTransaction.client_id == client_id,
                    WalletTransaction.transaction_type.in_([
                        TransactionType.MESSAGE_COST,
                        TransactionType.CAMPAIGN_COST, # CAMPAIGN_COST might be a sum of MESSAGE_COSTs or a separate fee
                        TransactionType.SERVICE_FEE
                    ]),
                    WalletTransaction.transaction_date >= start_date,
                    WalletTransaction.transaction_date <= end_date_inclusive
                )
            total_deductions = total_deductions_query.scalar() or decimal.Decimal("0.00")
            # Amounts for deductions are stored as negative, so abs() for reporting total deductions as positive.
            total_deductions_positive = abs(total_deductions)
            
            total_messages_sent_in_period = db.session.query(func.count(MessageLog.id)) \
                .join(Campaign, MessageLog.campaign_id == Campaign.id) \
                .filter(
                    Campaign.client_id == client_id,
                    MessageLog.direction == "outgoing",
                    MessageLog.status.in_([MessageStatus.SENT_TO_WHATSAPP, MessageStatus.DELIVERED, MessageStatus.READ]),
                    MessageLog.timestamp >= start_date,
                    MessageLog.timestamp <= end_date_inclusive
                ).scalar() or 0
            
            # Sum of actual MESSAGE_COST transactions for the period
            total_message_cost_value = db.session.query(func.sum(WalletTransaction.amount)) \
                .filter(
                    WalletTransaction.client_id == client_id,
                    WalletTransaction.transaction_type == TransactionType.MESSAGE_COST,
                    WalletTransaction.transaction_date >= start_date,
                    WalletTransaction.transaction_date <= end_date_inclusive
                ).scalar() or decimal.Decimal("0.00")
            
            avg_cost_per_message = (abs(total_message_cost_value) / total_messages_sent_in_period) \
                if total_messages_sent_in_period > 0 else decimal.Decimal("0.00")

            net_wallet_change = total_top_ups + total_deductions # total_deductions is already negative if summed directly
            
            # Placeholder for profit - requires more business logic (e.g. your cost vs client price)
            # For now, we can show net change or total service fees if applicable.
            daily_profit_placeholder = net_wallet_change 

            client_profile = ClientProfile.query.filter_by(user_id=client_id).first()
            current_balance = client_profile.wallet_balance if client_profile else decimal.Decimal("0.00")
            currency = client_profile.currency if client_profile else SYSTEM_DEFAULT_CURRENCY

            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_top_ups": float(total_top_ups),
                "total_deductions": float(total_deductions_positive),
                "net_wallet_change": float(net_wallet_change),
                "avg_cost_per_message": float(avg_cost_per_message),
                "daily_profit_placeholder": float(daily_profit_placeholder),
                "current_wallet_balance": float(current_balance),
                "currency": currency,
                "total_messages_sent_in_period": total_messages_sent_in_period
            }
        except Exception as e:
            logger.error(f"Error calculating financial summary for client {client_id}: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def get_campaign_performance_summary(client_id: int, campaign_id: int = None):
        """Calculates campaign performance summary for a client, optionally for a specific campaign."""
        try:
            query = db.session.query(
                Campaign.id.label("campaign_id"),
                Campaign.campaign_name,
                Campaign.status.label("campaign_status"),
                Campaign.total_recipients,
                func.count(MessageLog.id).label("total_messages_attempted"),
                func.sum(case((MessageLog.status.in_([MessageStatus.SENT_TO_WHATSAPP, MessageStatus.DELIVERED, MessageStatus.READ]), 1), else_=0)).label("messages_successfully_sent"),
                func.sum(case((MessageLog.status == MessageStatus.DELIVERED, 1), else_=0)).label("messages_delivered"),
                func.sum(case((MessageLog.status == MessageStatus.READ, 1), else_=0)).label("messages_read"),
                func.sum(case((MessageLog.status.in_([MessageStatus.FAILED_ON_SEND, MessageStatus.FAILED_INTERNAL_ERROR_ON_SEND, MessageStatus.FAILED_FROM_WHATSAPP]), 1), else_=0)).label("messages_failed")
            ).select_from(Campaign).outerjoin(MessageLog, Campaign.id == MessageLog.campaign_id)\
            .filter(Campaign.client_id == client_id)
            
            if campaign_id:
                query = query.filter(Campaign.id == campaign_id)
            
            query = query.group_by(Campaign.id, Campaign.campaign_name, Campaign.status, Campaign.total_recipients)\
                         .order_by(Campaign.created_at.desc())
            
            results = query.all()
            summary = []
            for row in results:
                sent_rate = (row.messages_successfully_sent / row.total_messages_attempted * 100) if row.total_messages_attempted > 0 else 0
                delivery_rate = (row.messages_delivered / row.messages_successfully_sent * 100) if row.messages_successfully_sent > 0 else 0
                read_rate = (row.messages_read / row.messages_delivered * 100) if row.messages_delivered > 0 else 0
                failure_rate = (row.messages_failed / row.total_messages_attempted * 100) if row.total_messages_attempted > 0 else 0
                
                summary.append({
                    "campaign_id": row.campaign_id,
                    "campaign_name": row.campaign_name,
                    "campaign_status": row.campaign_status,
                    "total_recipients": row.total_recipients,
                    "total_messages_attempted": row.total_messages_attempted,
                    "messages_successfully_sent": row.messages_successfully_sent,
                    "messages_delivered": row.messages_delivered,
                    "messages_read": row.messages_read,
                    "messages_failed": row.messages_failed,
                    "sent_rate_percentage": round(sent_rate, 2),
                    "delivery_rate_percentage": round(delivery_rate, 2),
                    "read_rate_percentage": round(read_rate, 2),
                    "failure_rate_percentage": round(failure_rate, 2)
                })
            return summary
        except Exception as e:
            logger.error(f"Error calculating campaign performance for client {client_id}: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def get_daily_transaction_summary(client_id: int, target_date: datetime):
        """Calculates daily financial transactions for a client for a specific date."""
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        top_ups_today = db.session.query(func.sum(WalletTransaction.amount)) \
            .filter(
                WalletTransaction.client_id == client_id,
                WalletTransaction.transaction_type == TransactionType.TOP_UP,
                WalletTransaction.transaction_date >= start_of_day,
                WalletTransaction.transaction_date <= end_of_day
            ).scalar() or decimal.Decimal("0.00")
        
        deductions_today_query = db.session.query(func.sum(WalletTransaction.amount)) \
            .filter(
                WalletTransaction.client_id == client_id,
                WalletTransaction.transaction_type.in_([TransactionType.MESSAGE_COST, TransactionType.CAMPAIGN_COST, TransactionType.SERVICE_FEE]),
                WalletTransaction.transaction_date >= start_of_day,
                WalletTransaction.transaction_date <= end_of_day
            )
        deductions_today = deductions_today_query.scalar() or decimal.Decimal("0.00")
        deductions_today_positive = abs(deductions_today)

        return {
            "date": target_date.isoformat(),
            "total_top_ups_today": float(top_ups_today),
            "total_deductions_today": float(deductions_today_positive)
        }


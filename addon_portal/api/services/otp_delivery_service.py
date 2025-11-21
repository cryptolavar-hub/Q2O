"""OTP Delivery Service - Sends OTP codes via email or SMS."""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from ..core.logging import get_logger
from ..core.settings import settings
from ..models.licensing import Tenant

LOGGER = get_logger(__name__)


def send_otp_email(tenant: Tenant, otp_code: str) -> bool:
    """Send OTP code via email.
    
    Args:
        tenant: Tenant instance with email address.
        otp_code: The 6-digit OTP code to send.
        
    Returns:
        True if email sent successfully, False otherwise.
    """
    if not settings.SMTP_ENABLED:
        LOGGER.warning(
            "smtp_disabled",
            extra={"tenant_id": tenant.id, "tenant_slug": tenant.slug},
        )
        return False
    
    if not tenant.email:
        LOGGER.error(
            "tenant_email_missing",
            extra={"tenant_id": tenant.id, "tenant_slug": tenant.slug},
        )
        return False
    
    if not all([settings.SMTP_HOST, settings.SMTP_USERNAME, settings.SMTP_PASSWORD, settings.SMTP_FROM_EMAIL]):
        LOGGER.error(
            "smtp_config_incomplete",
            extra={"tenant_id": tenant.id},
        )
        return False
    
    try:
        # Create email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your Q2O Login Code - {otp_code}"
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = tenant.email
        
        # Email body
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
              <h2 style="color: #8E44AD;">Your Q2O Login Code</h2>
              <p>Hello {tenant.name},</p>
              <p>Your one-time password (OTP) for logging into the Q2O Tenant Portal is:</p>
              <div style="background-color: #f4f4f4; padding: 20px; text-align: center; margin: 20px 0; border-radius: 5px;">
                <h1 style="color: #8E44AD; font-size: 32px; letter-spacing: 5px; margin: 0;">{otp_code}</h1>
              </div>
              <p>This code will expire in <strong>10 minutes</strong>.</p>
              <p>If you didn't request this code, please ignore this email.</p>
              <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
              <p style="color: #666; font-size: 12px;">This is an automated message from Q2O Platform. Please do not reply to this email.</p>
            </div>
          </body>
        </html>
        """
        
        text_body = f"""
        Your Q2O Login Code
        
        Hello {tenant.name},
        
        Your one-time password (OTP) for logging into the Q2O Tenant Portal is:
        
        {otp_code}
        
        This code will expire in 10 minutes.
        
        If you didn't request this code, please ignore this email.
        
        ---
        This is an automated message from Q2O Platform. Please do not reply to this email.
        """
        
        # Attach both plain text and HTML versions
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        # Send email
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        LOGGER.info(
            "otp_email_sent",
            extra={
                "tenant_id": tenant.id,
                "tenant_slug": tenant.slug,
                "email": tenant.email,
            },
        )
        return True
        
    except Exception as e:
        LOGGER.error(
            "otp_email_failed",
            extra={
                "tenant_id": tenant.id,
                "tenant_slug": tenant.slug,
                "error": str(e),
            },
        )
        return False


def send_otp_sms(tenant: Tenant, otp_code: str) -> bool:
    """Send OTP code via SMS.
    
    Args:
        tenant: Tenant instance with phone number.
        otp_code: The 6-digit OTP code to send.
        
    Returns:
        True if SMS sent successfully, False otherwise.
        
    Note:
        Currently returns False - SMS integration needs to be implemented
        with Twilio, AWS SNS, or similar service.
    """
    if not settings.SMS_ENABLED:
        LOGGER.warning(
            "sms_disabled",
            extra={"tenant_id": tenant.id, "tenant_slug": tenant.slug},
        )
        return False
    
    if not tenant.phone_number:
        LOGGER.error(
            "tenant_phone_missing",
            extra={"tenant_id": tenant.id, "tenant_slug": tenant.slug},
        )
        return False
    
    # TODO: Implement SMS sending via Twilio, AWS SNS, etc.
    LOGGER.warning(
        "sms_not_implemented",
        extra={
            "tenant_id": tenant.id,
            "tenant_slug": tenant.slug,
            "phone_number": tenant.phone_number,
        },
    )
    return False


def deliver_otp(tenant: Tenant, otp_code: str) -> bool:
    """Deliver OTP code to tenant based on their delivery preference.
    
    Args:
        tenant: Tenant instance.
        otp_code: The 6-digit OTP code to send.
        
    Returns:
        True if OTP delivered successfully via at least one method, False otherwise.
    """
    delivery_method = tenant.otp_delivery_method or "email"
    success = False
    
    if delivery_method in ("email", "both"):
        if send_otp_email(tenant, otp_code):
            success = True
    
    if delivery_method in ("sms", "whatsapp", "both"):
        if send_otp_sms(tenant, otp_code):
            success = True
    
    if not success:
        LOGGER.error(
            "otp_delivery_failed",
            extra={
                "tenant_id": tenant.id,
                "tenant_slug": tenant.slug,
                "delivery_method": delivery_method,
                "has_email": bool(tenant.email),
                "has_phone": bool(tenant.phone_number),
            },
        )
    
    return success


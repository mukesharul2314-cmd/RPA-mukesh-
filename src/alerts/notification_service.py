"""
Notification service for sending alerts via multiple channels
"""
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Optional imports for external services
try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
except ImportError:
    SendGridAPIClient = None
    Mail = None

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


@dataclass
class NotificationRecipient:
    """Notification recipient information"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    push_token: Optional[str] = None
    channels: List[NotificationChannel] = None
    location: Optional[Dict[str, float]] = None  # lat, lon for location-based alerts
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = [NotificationChannel.EMAIL]


@dataclass
class AlertNotification:
    """Alert notification data"""
    title: str
    message: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    alert_type: str  # FLOOD, EARTHQUAKE
    location: Dict[str, float]  # lat, lon
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict] = None


class NotificationService:
    """Service for sending notifications through multiple channels"""
    
    def __init__(self):
        self.email_config = self._load_email_config()
        self.sms_config = self._load_sms_config()
        self.recipients = []
        
    def _load_email_config(self) -> Dict:
        """Load email configuration"""
        return {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'from_email': os.getenv('ALERT_EMAIL_FROM', 'alerts@disaster-management.com'),
            'sendgrid_api_key': os.getenv('SENDGRID_API_KEY')
        }
    
    def _load_sms_config(self) -> Dict:
        """Load SMS configuration"""
        return {
            'twilio_account_sid': os.getenv('TWILIO_ACCOUNT_SID'),
            'twilio_auth_token': os.getenv('TWILIO_AUTH_TOKEN'),
            'twilio_phone_number': os.getenv('TWILIO_PHONE_NUMBER')
        }
    
    def add_recipient(self, recipient: NotificationRecipient):
        """Add a notification recipient"""
        self.recipients.append(recipient)
        logger.info(f"Added recipient: {recipient.name}")
    
    def remove_recipient(self, recipient_name: str):
        """Remove a notification recipient"""
        self.recipients = [r for r in self.recipients if r.name != recipient_name]
        logger.info(f"Removed recipient: {recipient_name}")
    
    async def send_alert(self, alert: AlertNotification, 
                        recipients: Optional[List[NotificationRecipient]] = None):
        """Send alert notification to recipients"""
        if recipients is None:
            recipients = self._get_relevant_recipients(alert)
        
        if not recipients:
            logger.warning("No recipients found for alert")
            return
        
        logger.info(f"Sending {alert.severity} {alert.alert_type} alert to {len(recipients)} recipients")
        
        # Send notifications through different channels
        for recipient in recipients:
            try:
                if NotificationChannel.EMAIL in recipient.channels and recipient.email:
                    await self._send_email(alert, recipient)
                
                if NotificationChannel.SMS in recipient.channels and recipient.phone:
                    await self._send_sms(alert, recipient)
                
                if NotificationChannel.PUSH in recipient.channels and recipient.push_token:
                    await self._send_push_notification(alert, recipient)
                    
            except Exception as e:
                logger.error(f"Error sending notification to {recipient.name}: {e}")
    
    def _get_relevant_recipients(self, alert: AlertNotification) -> List[NotificationRecipient]:
        """Get recipients relevant to the alert location and severity"""
        relevant_recipients = []
        
        for recipient in self.recipients:
            # Check if recipient should receive this alert based on:
            # 1. Location proximity
            # 2. Alert severity
            # 3. Alert type preferences
            
            if self._should_notify_recipient(recipient, alert):
                relevant_recipients.append(recipient)
        
        return relevant_recipients
    
    def _should_notify_recipient(self, recipient: NotificationRecipient, 
                               alert: AlertNotification) -> bool:
        """Determine if recipient should receive this alert"""
        # Always notify for CRITICAL alerts
        if alert.severity == 'CRITICAL':
            return True
        
        # Check location proximity if recipient has location
        if recipient.location:
            distance = self._calculate_distance(
                recipient.location, 
                alert.location
            )
            
            # Notification radius based on severity
            radius_km = {
                'LOW': 50,
                'MEDIUM': 100,
                'HIGH': 200,
                'CRITICAL': 500
            }.get(alert.severity, 100)
            
            return distance <= radius_km
        
        # Default to notify if no location specified
        return True
    
    def _calculate_distance(self, loc1: Dict[str, float], 
                          loc2: Dict[str, float]) -> float:
        """Calculate distance between two locations in kilometers"""
        from math import radians, sin, cos, sqrt, atan2
        
        lat1, lon1 = radians(loc1['lat']), radians(loc1['lon'])
        lat2, lon2 = radians(loc2['lat']), radians(loc2['lon'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return 6371 * c  # Earth's radius in km
    
    async def _send_email(self, alert: AlertNotification, 
                         recipient: NotificationRecipient):
        """Send email notification"""
        try:
            subject = f"[{alert.severity}] {alert.alert_type} Alert: {alert.title}"
            
            # Create email content
            html_content = self._create_email_html(alert, recipient)
            text_content = self._create_email_text(alert, recipient)
            
            # Try SendGrid first, fall back to SMTP
            if self.email_config['sendgrid_api_key'] and SendGridAPIClient:
                await self._send_email_sendgrid(subject, html_content, recipient.email)
            else:
                await self._send_email_smtp(subject, html_content, text_content, recipient.email)
                
            logger.info(f"Email sent to {recipient.email}")
            
        except Exception as e:
            logger.error(f"Error sending email to {recipient.email}: {e}")
            raise
    
    async def _send_email_sendgrid(self, subject: str, content: str, to_email: str):
        """Send email using SendGrid"""
        if not SendGridAPIClient:
            raise ImportError("SendGrid library not installed")
        
        message = Mail(
            from_email=self.email_config['from_email'],
            to_emails=to_email,
            subject=subject,
            html_content=content
        )
        
        sg = SendGridAPIClient(api_key=self.email_config['sendgrid_api_key'])
        response = sg.send(message)
        
        if response.status_code not in [200, 202]:
            raise Exception(f"SendGrid error: {response.status_code}")
    
    async def _send_email_smtp(self, subject: str, html_content: str, 
                              text_content: str, to_email: str):
        """Send email using SMTP"""
        msg = MimeMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.email_config['from_email']
        msg['To'] = to_email
        
        # Add text and HTML parts
        text_part = MimeText(text_content, 'plain')
        html_part = MimeText(html_content, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
            server.starttls()
            if self.email_config['username'] and self.email_config['password']:
                server.login(self.email_config['username'], self.email_config['password'])
            server.send_message(msg)
    
    async def _send_sms(self, alert: AlertNotification, 
                       recipient: NotificationRecipient):
        """Send SMS notification"""
        try:
            if not TwilioClient:
                raise ImportError("Twilio library not installed")
            
            if not all([self.sms_config['twilio_account_sid'], 
                       self.sms_config['twilio_auth_token'],
                       self.sms_config['twilio_phone_number']]):
                raise ValueError("Twilio configuration incomplete")
            
            client = TwilioClient(
                self.sms_config['twilio_account_sid'],
                self.sms_config['twilio_auth_token']
            )
            
            message_text = self._create_sms_text(alert, recipient)
            
            message = client.messages.create(
                body=message_text,
                from_=self.sms_config['twilio_phone_number'],
                to=recipient.phone
            )
            
            logger.info(f"SMS sent to {recipient.phone}: {message.sid}")
            
        except Exception as e:
            logger.error(f"Error sending SMS to {recipient.phone}: {e}")
            raise
    
    async def _send_push_notification(self, alert: AlertNotification,
                                    recipient: NotificationRecipient):
        """Send push notification (placeholder for implementation)"""
        # This would integrate with services like Firebase Cloud Messaging,
        # Apple Push Notification Service, etc.
        logger.info(f"Push notification would be sent to {recipient.push_token}")
    
    def _create_email_html(self, alert: AlertNotification, 
                          recipient: NotificationRecipient) -> str:
        """Create HTML email content"""
        severity_colors = {
            'LOW': '#28a745',
            'MEDIUM': '#ffc107',
            'HIGH': '#fd7e14',
            'CRITICAL': '#dc3545'
        }
        
        color = severity_colors.get(alert.severity, '#6c757d')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Disaster Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">{alert.severity} {alert.alert_type} ALERT</h1>
                </div>
                <div style="padding: 20px;">
                    <h2 style="color: #333; margin-top: 0;">{alert.title}</h2>
                    <p style="color: #666; line-height: 1.6;">{alert.message}</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #333;">Alert Details</h3>
                        <p><strong>Type:</strong> {alert.alert_type}</p>
                        <p><strong>Severity:</strong> {alert.severity}</p>
                        <p><strong>Location:</strong> {alert.location['lat']:.4f}, {alert.location['lon']:.4f}</p>
                        <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                        {f"<p><strong>Expires:</strong> {alert.expires_at.strftime('%Y-%m-%d %H:%M:%S')} UTC</p>" if alert.expires_at else ""}
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <p style="color: #666; font-size: 14px;">
                            This is an automated alert from the Disaster Management System.<br>
                            Please take appropriate safety measures.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_email_text(self, alert: AlertNotification, 
                          recipient: NotificationRecipient) -> str:
        """Create plain text email content"""
        return f"""
{alert.severity} {alert.alert_type} ALERT

{alert.title}

{alert.message}

Alert Details:
- Type: {alert.alert_type}
- Severity: {alert.severity}
- Location: {alert.location['lat']:.4f}, {alert.location['lon']:.4f}
- Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
{f"- Expires: {alert.expires_at.strftime('%Y-%m-%d %H:%M:%S')} UTC" if alert.expires_at else ""}

This is an automated alert from the Disaster Management System.
Please take appropriate safety measures.
        """
    
    def _create_sms_text(self, alert: AlertNotification, 
                        recipient: NotificationRecipient) -> str:
        """Create SMS text content"""
        return f"""
{alert.severity} {alert.alert_type} ALERT

{alert.title}

Location: {alert.location['lat']:.3f}, {alert.location['lon']:.3f}
Time: {datetime.utcnow().strftime('%m/%d %H:%M')}

Take appropriate safety measures.
        """

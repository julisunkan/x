"""
SMTP Email Client - Handles all email sending functionality
"""

import smtplib
import ssl
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from models.settings import AppSettings

class SMTPClient:
    """SMTP client for sending emails"""
    
    def __init__(self):
        self.settings = AppSettings.get_settings()
        
    def get_smtp_config(self):
        """Get SMTP configuration from database"""
        return {
            'server': self.settings.smtp_server,
            'port': self.settings.smtp_port,
            'username': self.settings.smtp_username,
            'password': self.settings.smtp_password,
            'use_tls': self.settings.smtp_use_tls,
            'from_email': self.settings.smtp_from_email,
            'from_name': self.settings.smtp_from_name
        }
    
    def test_connection(self):
        """Test SMTP connection and return status"""
        try:
            config = self.get_smtp_config()
            
            # Validate required fields
            if not all([config['server'], config['port'], config['username'], 
                       config['password'], config['from_email']]):
                return {
                    'success': False,
                    'message': 'Missing required SMTP configuration fields'
                }
            
            # Create SMTP connection
            if config['use_tls']:
                # Use TLS (usually port 587)
                server = smtplib.SMTP(config['server'], config['port'])
                server.starttls()
            else:
                # Use SSL (usually port 465)
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(config['server'], config['port'], context=context)
            
            # Login
            server.login(config['username'], config['password'])
            
            # Close connection
            server.quit()
            
            logging.info("SMTP connection test successful")
            return {
                'success': True,
                'message': 'SMTP connection successful! Email settings are working correctly.'
            }
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP Authentication failed: {str(e)}"
            logging.error(error_msg)
            return {
                'success': False,
                'message': 'Authentication failed. Please check your username and password.'
            }
            
        except smtplib.SMTPConnectError as e:
            error_msg = f"SMTP Connection failed: {str(e)}"
            logging.error(error_msg)
            return {
                'success': False,
                'message': 'Cannot connect to SMTP server. Please check server and port settings.'
            }
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP Error: {str(e)}"
            logging.error(error_msg)
            return {
                'success': False,
                'message': f'SMTP error: {str(e)}'
            }
            
        except Exception as e:
            error_msg = f"Unexpected error during SMTP test: {str(e)}"
            logging.error(error_msg)
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            }
    
    def send_email(self, to_email, subject, body, is_html=False, attachments=None):
        """Send email using SMTP"""
        try:
            config = self.get_smtp_config()
            
            # Validate configuration
            if not all([config['server'], config['port'], config['username'], 
                       config['password'], config['from_email']]):
                logging.error("Missing required SMTP configuration")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{config['from_name']} <{config['from_email']}>" if config['from_name'] else config['from_email']
            msg['To'] = to_email
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    if isinstance(attachment, dict) and 'filename' in attachment and 'content' in attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment['content'])
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {attachment["filename"]}'
                        )
                        msg.attach(part)
            
            # Create SMTP connection and send
            if config['use_tls']:
                server = smtplib.SMTP(config['server'], config['port'])
                server.starttls()
            else:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(config['server'], config['port'], context=context)
            
            server.login(config['username'], config['password'])
            server.send_message(msg)
            server.quit()
            
            logging.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_test_email(self, to_email=None):
        """Send a test email to verify SMTP configuration"""
        if not to_email:
            config = self.get_smtp_config()
            to_email = config['from_email']  # Send to self by default
        
        subject = "SMTP Test Email - RoseCoin Platform"
        body = """
        <html>
        <body>
            <h2>SMTP Configuration Test</h2>
            <p>This is a test email to verify that your SMTP settings are working correctly.</p>
            <p><strong>Test Details:</strong></p>
            <ul>
                <li>Platform: RoseCoin Mining Platform</li>
                <li>Test Time: {}</li>
                <li>Status: SMTP Configuration Successful</li>
            </ul>
            <p>If you received this email, your SMTP settings are configured correctly and emails will be sent successfully.</p>
            <hr>
            <p><em>This is an automated test email from RoseCoin platform.</em></p>
        </body>
        </html>
        """.format(str(datetime.now()))
        
        return self.send_email(to_email, subject, body, is_html=True)

# Global instance
smtp_client = SMTPClient()
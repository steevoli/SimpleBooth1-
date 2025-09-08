import os
import smtplib
from email.message import EmailMessage
import logging

logger = logging.getLogger(__name__)

def send_email(photo_path, config):
    """Send photo as email attachment using settings from config.

    Returns tuple (success: bool, error_message: str|None).
    """
    recipient = config.get('email_recipient')
    if not recipient:
        return False, "Destinataire non configuré"

    smtp_server = config.get('smtp_server', 'localhost')
    smtp_port = config.get('smtp_port', 25)
    smtp_username = config.get('smtp_username', '')
    smtp_password = config.get('smtp_password', '')
    smtp_use_tls = config.get('smtp_use_tls', False)
    sender = config.get('email_sender', smtp_username or 'photobooth@example.com')

    msg = EmailMessage()
    msg['Subject'] = 'Photo du photobooth'
    msg['From'] = sender
    msg['To'] = recipient
    msg.set_content('Veuillez trouver la photo en pièce jointe.')

    try:
        with open(photo_path, 'rb') as f:
            img_data = f.read()
        msg.add_attachment(
            img_data,
            maintype='image',
            subtype='jpeg',
            filename=os.path.basename(photo_path)
        )

        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            if smtp_use_tls:
                server.starttls()
            if smtp_username:
                server.login(smtp_username, smtp_password)
            server.send_message(msg)
        logger.info('[EMAIL] Photo envoyée avec succès')
        return True, None
    except Exception as e:
        logger.info(f'[EMAIL] Erreur lors de l\'envoi: {e}')
        return False, str(e)

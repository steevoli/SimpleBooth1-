import os
import re
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

    smtp_server = config.get('smtp_server', '').strip()
    smtp_port = config.get('smtp_port', 25)
    smtp_username = config.get('smtp_username', '').strip()
    smtp_password = config.get('smtp_password', '').strip()
    sender = config.get('email_sender', smtp_username or 'photobooth@example.com')

    email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(email_regex, recipient):
        return False, "Adresse destinataire invalide"
    if sender and not re.match(email_regex, sender):
        return False, "Adresse expéditeur invalide"
    if not smtp_server:
        return False, "Serveur SMTP manquant"
    try:
        smtp_port = int(smtp_port)
    except ValueError:
        return False, "Port SMTP invalide"
    if smtp_username and not smtp_password:
        return False, "Mot de passe manquant"
    if smtp_password and not smtp_username:
        return False, "Identifiant manquant"

    subject = config.get('email_subject', 'Photo du photobooth')
    msg = EmailMessage()
    msg['Subject'] = subject
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

        def _send(port):
            if port == 465:
                smtp_class = smtplib.SMTP_SSL
            else:
                smtp_class = smtplib.SMTP
            with smtp_class(smtp_server, port, timeout=10) as server:
                server.ehlo()
                if port != 465 and server.has_extn('starttls'):
                    try:
                        server.starttls()
                        server.ehlo()
                    except Exception as tls_error:
                        logger.info(f"[EMAIL] Échec initialisation TLS: {tls_error}")
                if smtp_username:
                    server.login(smtp_username, smtp_password)
                server.send_message(msg)

        try:
            _send(smtp_port)
        except Exception as first_error:
            if smtp_port == 465:
                logger.info('[EMAIL] Port 465 indisponible, tentative sur 587')
                try:
                    _send(587)
                except Exception as second_error:
                    logger.info(f"[EMAIL] Échec sur 587: {second_error}")
                    return False, str(second_error)
            else:
                logger.info(f"[EMAIL] Échec envoi: {first_error}")
                return False, str(first_error)
        logger.info('[EMAIL] Photo envoyée avec succès')
        return True, None
    except Exception as e:
        logger.info(f"[EMAIL] Erreur lors de l'envoi: {e}")
        return False, str(e)

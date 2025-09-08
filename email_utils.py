import os
import re
import smtplib
from email.message import EmailMessage
import logging
from config_utils import load_config

logger = logging.getLogger(__name__)


def send_email(photo_path, settings=None):
    """Send photo as email attachment.

    Parameters
    ----------
    photo_path: str
        Path to the photo to send.
    settings: dict | None
        Optional dictionary containing SMTP and email fields. If omitted,
        configuration is loaded from ``config.json``.

    Returns
    -------
    tuple(bool, str | None)
        Success flag and optional error message.
    """

    if settings is None:
        cfg = load_config()
        settings = {
            'smtp_server': cfg.get('smtp_server', ''),
            'smtp_port': cfg.get('smtp_port', 25),
            'smtp_username': cfg.get('smtp_username', ''),
            'smtp_password': cfg.get('smtp_password', ''),
            'sender': cfg.get('email_sender') or cfg.get('smtp_username', ''),
            'recipient': cfg.get('email_recipient')
            or cfg.get('email_sender')
            or cfg.get('smtp_username', ''),
            'subject': cfg.get('email_subject', 'Photo du photobooth'),
        }

    recipient = (settings or {}).get('recipient', '').strip()
    sender = (settings or {}).get('sender', '').strip()
    smtp_server = (settings or {}).get('smtp_server', '').strip()
    smtp_port = (settings or {}).get('smtp_port', 25)
    smtp_username = (settings or {}).get('smtp_username', '').strip()
    smtp_password = (settings or {}).get('smtp_password', '').strip()
    subject = (settings or {}).get('subject', 'Photo du photobooth').strip()

    email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not recipient or not re.match(email_regex, recipient):
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

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender or smtp_username or 'photobooth@example.com'
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
            smtp_class = smtplib.SMTP_SSL if port == 465 else smtplib.SMTP
            with smtp_class(smtp_server, port, timeout=10) as server:
                server.ehlo()
                if port != 465 and server.has_extn('starttls'):
                    try:
                        server.starttls()
                        server.ehlo()
                    except Exception as tls_error:  # pragma: no cover
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
    except Exception as e:  # pragma: no cover - dépend de l'environnement
        logger.info(f"[EMAIL] Erreur lors de l'envoi: {e}")
        return False, str(e)

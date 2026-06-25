from __future__ import annotations

import logging

from app.infrastructure.email.provider import EmailProvider, EmailMessage

logger = logging.getLogger(__name__)


class SMTPEmailProvider(EmailProvider):
    async def send(self, message: EmailMessage) -> bool:
        logger.info(f"[STUB] Would send email to {message.to}: {message.subject}")
        return True

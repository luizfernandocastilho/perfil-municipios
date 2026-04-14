"""Notificações Slack para pipelines ETL."""

import os
from datetime import datetime

import httpx

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")


async def notify_etl_success(
    fonte_id: str,
    fonte_nome: str,
    tabela: str,
    registros: int,
    duracao_seg: float,
):
    if not SLACK_WEBHOOK:
        return

    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"✅ ETL concluído: {fonte_id}"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Fonte:*\n{fonte_nome}"},
                    {"type": "mrkdwn", "text": f"*Tabela:*\n`{tabela}`"},
                    {"type": "mrkdwn", "text": f"*Registros:*\n{registros:,}"},
                    {"type": "mrkdwn", "text": f"*Duração:*\n{duracao_seg:.1f}s"},
                ],
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
                ],
            },
        ]
    }

    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK, json=payload)


async def notify_etl_failure(
    fonte_id: str,
    fonte_nome: str,
    erro: str,
):
    if not SLACK_WEBHOOK:
        return

    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🚨 ETL FALHOU: {fonte_id}"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Fonte:* {fonte_nome}\n*Erro:*\n```{erro[:500]}```",
                },
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
                ],
            },
        ]
    }

    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK, json=payload)

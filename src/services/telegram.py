import httpx
from src.core.config import settings
from src.core.logging_config import logger

class TelegramService:
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def send_invoice(self, chat_id: int, title: str, description: str, payload: str, price_cents: int):
        data = {
            "chat_id": chat_id,
            "title": title,
            "description": description,
            "payload": payload,
            "provider_token": settings.TELEGRAM_PROVIDER_TOKEN,
            "currency": "BRL",
            "prices": [{"label": "Conversão PDF -> CSV", "amount": price_cents}],
            "start_parameter": f"start-{payload}"
        }
        try:
            response = await self.client.post("/sendInvoice", json=data)
            response.raise_for_status()
            logger.info(f"Invoice sent to {chat_id} for payload {payload}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send invoice: {e}")
            return None

    async def answer_pre_checkout_query(self, pre_checkout_query_id: str, ok: bool = True):
        data = {
            "pre_checkout_query_id": pre_checkout_query_id,
            "ok": ok
        }
        try:
            await self.client.post("/answerPreCheckoutQuery", json=data)
            logger.info(f"Answered pre_checkout_query {pre_checkout_query_id}")
        except Exception as e:
            logger.error(f"Failed to answer pre_checkout_query: {e}")

    async def send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown"):
        data = {
            "chat_id": chat_id, 
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        try:
            response = await self.client.post("/sendMessage", json=data)
            response.raise_for_status()
            logger.info(f"Message sent to {chat_id}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return None

    async def send_message_with_keyboard(self, chat_id: int, text: str, keyboard: dict, parse_mode: str = "Markdown"):
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
            "reply_markup": keyboard
        }
        try:
            response = await self.client.post("/sendMessage", json=data)
            response.raise_for_status()
            logger.info(f"Message with keyboard sent to {chat_id}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send message with keyboard: {e}")
            return None

    async def get_file_path(self, file_id: str):
        try:
            response = await self.client.post("/getFile", json={"file_id": file_id})
            response.raise_for_status()
            result = response.json().get("result", {})
            return result.get("file_path")
        except Exception as e:
            logger.error(f"Failed to get file path: {e}")
            return None
    
    async def download_file(self, file_path: str, destination: str):
        url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                with open(destination, "wb") as f:
                    f.write(response.content)
            return True
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            return False

    async def send_document(self, chat_id: int, document_path: str, caption: str = ""):
        try:
            with open(document_path, "rb") as f:
                files = {"document": f}
                data = {"chat_id": chat_id, "caption": caption}
                response = await self.client.post("/sendDocument", data=data, files=files)
                response.raise_for_status()
                logger.info(f"Document sent to {chat_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to send document: {e}")
            return False

from pathlib import Path
import os

from src.core.celery_app import celery_app
from src.core.config import settings
from src.services.document_converter import DocumentConverterService
from src.services.pdf_reader import PDFReader
from src.services.csv_writer import CSVWriter

@celery_app.task(bind=True, name="convert_document")
def convert_document_task(self, input_path_str: str):
    try:
        input_path = Path(input_path_str)
        output_filename = input_path.stem + ".csv"
        output_path = Path(settings.OUTPUT_DIR) / output_filename
        
        # Instanciar serviços
        pdf_reader = PDFReader()
        csv_writer = CSVWriter()
        converter = DocumentConverterService(pdf_reader, csv_writer)
        
        # Converter
        converter.convert(input_path, output_path)
        
        return {
            "status": "success",
            "output_path": str(output_path),
            "filename": output_filename
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@celery_app.task(bind=True, name="process_telegram_order")
def process_telegram_order(self, order_id: str):
    import asyncio
    from sqlalchemy.future import select
    from src.core.database import AsyncSessionLocal
    from src.models.order import Order
    from src.services.telegram import TelegramService
    
    # Helper to run async code in sync celery task
    def run_async(coro):
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

    async def _process():
        telegram_service = TelegramService()
        async with AsyncSessionLocal() as db:
            # Get Order
            result = await db.execute(select(Order).where(Order.id == order_id))
            order = result.scalars().first()
            
            if not order:
                logger.error(f"Order {order_id} not found in worker")
                return
            
            try:
                # Download File
                file_path = await telegram_service.get_file_path(order.file_id)
                if not file_path:
                    raise Exception("Failed to get file path from Telegram")
                
                local_pdf_path = Path(settings.UPLOAD_DIR) / f"{order_id}.pdf"
                await telegram_service.download_file(file_path, str(local_pdf_path))
                order.pdf_path = str(local_pdf_path)
                
                # Convert
                output_filename = f"{order_id}.csv"
                output_path = Path(settings.OUTPUT_DIR) / output_filename
                
                pdf_reader = PDFReader()
                csv_writer = CSVWriter()
                converter = DocumentConverterService(pdf_reader, csv_writer)
                converter.convert(local_pdf_path, output_path)
                
                order.csv_path = str(output_path)
                order.status = "completed"
                await db.commit()
                
                # Send Document
                await telegram_service.send_document(
                    order.chat_id, 
                    str(output_path), 
                    caption=f"Seu arquivo convertido (Pedido {order_id})"
                )
                
            except Exception as e:
                logger.error(f"Error processing order {order_id}: {e}")
                order.status = "failed"
                order.error = str(e)
                await db.commit()
                await telegram_service.send_message(
                    order.chat_id, 
                    f"Erro ao processar seu pedido: {e}"
                )

    try:
        run_async(_process())
    except Exception as e:
        logger.error(f"Fatal error in worker task: {e}")


@celery_app.task(bind=True, name="simulate_test_payment")
def simulate_test_payment(self, order_id: str):
    """Simulate payment for test user after 5 seconds"""
    import asyncio
    import time
    from sqlalchemy.future import select
    from src.core.database import AsyncSessionLocal
    from src.models.order import Order, Payment
    from src.services.telegram import TelegramService
    from src.core.logging_config import logger
    
    # Wait 5 seconds
    time.sleep(5)
    
    def run_async(coro):
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

    async def _simulate_payment():
        telegram_service = TelegramService()
        async with AsyncSessionLocal() as db:
            # Get Order
            result = await db.execute(select(Order).where(Order.id == order_id))
            order = result.scalars().first()
            
            if not order:
                logger.error(f"Order {order_id} not found for test payment")
                return
            
            if order.status != "pending_payment":
                logger.warning(f"Order {order_id} is not pending payment, skipping test")
                return
            
            try:
                # Update order status
                order.status = "paid"
                order.provider_payment_id = f"test_payment_{order_id}"
                
                # Record test payment
                test_payment = Payment(
                    order_id=order.id,
                    amount_cents=5000,
                    currency="BRL",
                    provider_payload={"test": True, "simulated": True},
                    status="success"
                )
                db.add(test_payment)
                await db.commit()
                
                # Notify user
                await telegram_service.send_message(
                    order.chat_id,
                    "✅ **[MODO TESTE] Pagamento simulado!** Iniciando conversão do seu arquivo..."
                )
                
                # Trigger processing
                process_telegram_order.delay(str(order.id))
                
                logger.info(f"Test payment simulated for order {order_id}")
                
            except Exception as e:
                logger.error(f"Error simulating test payment for order {order_id}: {e}")

    try:
        run_async(_simulate_payment())
    except Exception as e:
        logger.error(f"Fatal error in test payment simulation: {e}")


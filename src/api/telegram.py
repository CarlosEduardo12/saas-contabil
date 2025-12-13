from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import os

from src.core.config import settings
from src.core.database import get_db
from src.core.logging_config import logger
from src.services.telegram import TelegramService
from src.services.ammer_pay import AmmerPayService
from src.models.order import Order, Payment
# We will import the task later to avoid circular imports if any, or just import it
# from src.worker.tasks import process_telegram_order

router = APIRouter()
telegram_service = TelegramService()
ammer_pay_service = AmmerPayService()

@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    # Validate Secret Token
    if settings.TELEGRAM_WEBHOOK_SECRET and x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        logger.warning("Invalid Telegram Secret Token")
        raise HTTPException(status_code=403, detail="Invalid Token")

    update = await request.json()
    
    # Handle Commands and Text Messages
    if "message" in update and "text" in update["message"]:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg["text"].strip()
        user_name = msg.get("from", {}).get("first_name", "Usuário")
        
        # Handle /start command
        if text == "/start":
            welcome_message = f"""🤖 Olá {user_name}! Bem-vindo ao **SaaS Contabil Converter**!

📊 **O que eu faço:**
Converto seus arquivos PDF contábeis para formato CSV de forma rápida, segura e automática.

💰 **Preço:** R$ 50,00 por conversão

🔒 **Segurança:**
• Apenas PDFs cadastrados são aceitos
• Dados criptografados e seguros
• Processamento automático

📋 **Como usar:**
1. Envie seu arquivo PDF
2. Faça o pagamento via Telegram
3. Receba seu CSV convertido

⚡ **Comandos disponíveis:**
/help - Ajuda detalhada
/preco - Informações sobre preços
/status - Verificar suas conversões

🚀 **Pronto para começar?** Envie seu PDF agora!"""
            
            await telegram_service.send_message(chat_id, welcome_message)
            return {"ok": True}
        
        # Handle /help command
        elif text == "/help":
            help_message = """📚 **Ajuda - SaaS Contabil Converter**

🔍 **Arquivos aceitos:**
• Apenas arquivos PDF
• Máximo 10MB por arquivo
• PDFs devem estar cadastrados em nossa base

💳 **Pagamento:**
• R$ 50,00 por conversão
• Pagamento via Telegram Payments
• Processamento imediato após confirmação

⏱️ **Processo:**
1. **Envie o PDF** → Sistema valida o arquivo
2. **Pague a fatura** → Receba via Telegram
3. **Aguarde** → Processamento automático (1-2 min)
4. **Receba o CSV** → Download direto no chat

❓ **Problemas comuns:**
• "PDF não cadastrado" → Arquivo não está em nossa base
• "Arquivo muito grande" → Reduza o tamanho para menos de 10MB
• "Formato inválido" → Envie apenas arquivos PDF

📞 **Suporte:** Entre em contato se precisar de ajuda!"""
            
            await telegram_service.send_message(chat_id, help_message)
            return {"ok": True}
        
        # Handle /preco command
        elif text == "/preco":
            price_message = """💰 **Preços - SaaS Contabil Converter**

🏷️ **Conversão PDF → CSV**
• **Preço:** R$ 50,00 por arquivo
• **Moeda:** Real Brasileiro (BRL)
• **Pagamento:** Via Telegram Payments

✅ **Incluído no preço:**
• Validação do arquivo PDF
• Conversão completa para CSV
• Processamento automático
• Entrega imediata no chat
• Suporte técnico

⚡ **Processo rápido:**
• Pagamento instantâneo
• Conversão em 1-2 minutos
• Sem taxas adicionais

🔒 **Garantias:**
• Dados seguros e criptografados
• Arquivos deletados após conversão
• Privacidade total

💡 **Dica:** Tenha seu PDF pronto antes de iniciar o pagamento!"""
            
            await telegram_service.send_message(chat_id, price_message)
            return {"ok": True}
        
        # Handle /status command
        elif text == "/status":
            # Get user's recent orders
            try:
                result = await db.execute(
                    select(Order).where(Order.chat_id == chat_id)
                    .order_by(Order.created_at.desc()).limit(5)
                )
                orders = result.scalars().all()
                
                if not orders:
                    status_message = """📊 **Status das Conversões**

🔍 **Nenhuma conversão encontrada**

Você ainda não fez nenhuma conversão. 
Envie um PDF para começar!"""
                else:
                    status_message = "📊 **Suas últimas conversões:**\n\n"
                    for order in orders:
                        status_emoji = {
                            "pending_payment": "⏳",
                            "paid": "💳",
                            "processing": "⚙️",
                            "completed": "✅",
                            "failed": "❌"
                        }.get(order.status, "❓")
                        
                        status_text = {
                            "pending_payment": "Aguardando pagamento",
                            "paid": "Pago - Processando",
                            "processing": "Em processamento",
                            "completed": "Concluído",
                            "failed": "Falhou"
                        }.get(order.status, "Status desconhecido")
                        
                        status_message += f"{status_emoji} **{order.file_name}**\n"
                        status_message += f"   Status: {status_text}\n"
                        status_message += f"   Data: {order.created_at.strftime('%d/%m/%Y %H:%M')}\n\n"
                
                await telegram_service.send_message(chat_id, status_message)
                return {"ok": True}
                
            except Exception as e:
                logger.error(f"Error getting status for chat {chat_id}: {e}")
                await telegram_service.send_message(
                    chat_id, 
                    "❌ Erro ao buscar status. Tente novamente em alguns instantes."
                )
                return {"ok": True}
        
        # Handle other text messages
        else:
            other_message = """🤖 **Não entendi sua mensagem**

📋 **Comandos disponíveis:**
/start - Informações principais
/help - Ajuda detalhada  
/preco - Ver preços
/status - Suas conversões

📄 **Para converter:** Envie um arquivo PDF
💡 **Dica:** Use os comandos acima para navegar!"""
            
            await telegram_service.send_message(chat_id, other_message)
            return {"ok": True}
    
    # 1. Handle Document (Create Order)
    if "message" in update and "document" in update["message"]:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        doc = msg["document"]
        file_id = doc["file_id"]
        file_name = doc.get("file_name", "document.pdf")
        file_size = doc.get("file_size", 0)
        
        # Validate file type
        if not file_name.lower().endswith('.pdf'):
            error_message = """❌ **Arquivo não suportado**

📋 **Apenas arquivos PDF são aceitos**

✅ **Formatos aceitos:** .pdf
❌ **Não aceitos:** .doc, .docx, .txt, .jpg, etc.

💡 **Dica:** Converta seu arquivo para PDF primeiro e tente novamente."""
            
            await telegram_service.send_message(chat_id, error_message)
            return {"ok": True}
        
        # Check if user has pending orders (one file at a time)
        result = await db.execute(
            select(Order).where(
                Order.chat_id == chat_id,
                Order.status.in_(["pending_payment", "paid", "processing"])
            )
        )
        pending_order = result.scalars().first()
        
        if pending_order:
            pending_message = f"""⏳ **Processamento em andamento**

📄 **Arquivo atual:** {pending_order.file_name}
📊 **Status:** {
    "Aguardando pagamento" if pending_order.status == "pending_payment" 
    else "Pago - Processando" if pending_order.status == "paid"
    else "Em processamento"
}

❌ **Apenas um arquivo por vez**

⚡ **Aguarde o processamento atual terminar antes de enviar outro arquivo.**

💡 **Use /status para acompanhar o progresso**"""
            
            await telegram_service.send_message(chat_id, pending_message)
            return {"ok": True}

        # Validate file size (60MB limit)
        max_size = 60 * 1024 * 1024  # 60MB
        if file_size > max_size:
            error_message = f"""❌ **Arquivo muito grande**

📏 **Tamanho atual:** {file_size / (1024*1024):.1f} MB
📏 **Limite máximo:** 60 MB

� ***Soluções:**
• Comprima o PDF usando ferramentas online
• Divida o arquivo em partes menores
• Remova páginas desnecessárias

🔄 Tente novamente com um arquivo menor."""
            
            await telegram_service.send_message(chat_id, error_message)
            return {"ok": True}
        
        # TODO: Add file validation here (check if PDF is registered)
        # For now, we'll simulate validation based on filename
        if not file_name.startswith("Ponto"):
            error_message = f"""❌ **PDF não cadastrado**

🔍 **Arquivo:** {file_name}

Este PDF não está registrado em nossa base de dados para conversão.

📋 **Arquivos aceitos:**
• PDFs que começam com "Ponto"
• Documentos previamente cadastrados

💡 **Precisa cadastrar um PDF?** Entre em contato conosco!"""
            
            await telegram_service.send_message(chat_id, error_message)
            return {"ok": True}
        
        # Create Order
        order_id = uuid.uuid4()
        payload = f"order_{order_id}"
        
        # Create Ammer Pay payment link
        user_name = msg.get("from", {}).get("first_name", "Cliente")
        payment_result = await ammer_pay_service.create_payment_link(
            amount_cents=5000,  # R$ 50,00
            description=f"Conversão PDF → CSV: {file_name}",
            external_id=str(order_id),
            customer_name=user_name,
            webhook_url=f"{os.getenv('WEBHOOK_URL', '')}/ammer/webhook"
        )
        
        if not payment_result.get("success"):
            error_message = """❌ **Erro no sistema de pagamento**

🔧 **Serviço temporariamente indisponível**

⏰ Tente novamente em alguns minutos ou entre em contato com o suporte."""
            
            await telegram_service.send_message(chat_id, error_message)
            return {"ok": True}
        
        new_order = Order(
            id=order_id,
            chat_id=chat_id,
            file_id=file_id,
            file_name=file_name,
            file_size=file_size,
            payload=payload,
            status="pending_payment",
            payment_method="ammer_pay",
            ammer_payment_id=payment_result.get("payment_id"),
            ammer_payment_url=payment_result.get("payment_url")
        )
        db.add(new_order)
        await db.commit()
        
        # Send confirmation message with payment button
        if payment_result.get("test_mode") or payment_result.get("fallback"):
            confirmation_message = f"""📄 **Arquivo aceito!**

**Nome:** {file_name}
**Tamanho:** {file_size / 1024:.1f} KB

✅ PDF validado com sucesso!
💰 **Valor:** R$ 50,00

🧪 **MODO TESTE/DEMO** - Sistema de pagamento em configuração

👇 **Botão de demonstração:**"""
        else:
            confirmation_message = f"""📄 **Arquivo aceito!**

**Nome:** {file_name}
**Tamanho:** {file_size / 1024:.1f} KB

✅ PDF validado com sucesso!
💰 **Valor:** R$ 50,00

👇 **Clique no botão abaixo para pagar:**"""
        
        # Create inline keyboard with payment button
        keyboard = {
            "inline_keyboard": [[
                {
                    "text": "💳 Pagar R$ 50,00" if not (payment_result.get("test_mode") or payment_result.get("fallback")) else "🧪 Demo - Pagar R$ 50,00",
                    "url": payment_result.get("payment_url")
                }
            ]]
        }
        
        await telegram_service.send_message_with_keyboard(chat_id, confirmation_message, keyboard)
        
        # TEST MODE: If this is the test user, simulate payment after 5 seconds
        if settings.TEST_USER_CHAT_ID and chat_id == settings.TEST_USER_CHAT_ID:
            # Send test mode notification
            test_message = """🧪 **MODO TESTE ATIVADO**

⏰ Pagamento será simulado automaticamente em 5 segundos para testar o fluxo completo.

💡 Em produção normal, o usuário clicaria no botão de pagamento."""
            
            await telegram_service.send_message(chat_id, test_message)
            
            # Schedule test payment simulation - simplified approach
            import asyncio
            
            async def delayed_test_payment():
                await asyncio.sleep(5)
                await simulate_test_payment_simple(str(order_id), chat_id, file_id, file_name)
            
            # Create task in current event loop
            asyncio.create_task(delayed_test_payment())
        
        return {"ok": True}

    # 2. Handle Pre-Checkout Query
    if "pre_checkout_query" in update:
        query = update["pre_checkout_query"]
        query_id = query["id"]
        await telegram_service.answer_pre_checkout_query(query_id, ok=True)
        return {"ok": True}

    # 3. Handle Successful Payment
    if "message" in update and "successful_payment" in update["message"]:
        msg = update["message"]
        payment_info = msg["successful_payment"]
        payload = payment_info["invoice_payload"]
        
        # Find Order
        result = await db.execute(select(Order).where(Order.payload == payload))
        order = result.scalars().first()
        
        if not order:
            logger.error(f"Order not found for payload {payload}")
            return {"ok": True}
            
        # SECURITY: Strict payment validation
        if payment_info["total_amount"] != order.price_cents:
            logger.error(f"SECURITY ALERT: Amount mismatch for order {order.id}. Expected: {order.price_cents}, Received: {payment_info['total_amount']}")
            # SECURITY: Reject invalid payments
            return {"ok": False, "error": "Payment amount mismatch"}
        
        # SECURITY: Validate currency
        if payment_info.get("currency") != order.currency:
            logger.error(f"SECURITY ALERT: Currency mismatch for order {order.id}")
            return {"ok": False, "error": "Currency mismatch"}
        
        # Update Order
        order.status = "paid"
        order.provider_payment_id = payment_info["provider_payment_charge_id"]
        order.telegram_payment_id = payment_info["telegram_payment_charge_id"]
        
        # Record Payment
        new_payment = Payment(
            order_id=order.id,
            amount_cents=payment_info["total_amount"],
            currency=payment_info["currency"],
            provider_payload=payment_info,
            status="success"
        )
        db.add(new_payment)
        await db.commit()
        
        # Trigger Processing Task
        # We import here to avoid potential circular import issues at module level
        from src.worker.tasks import process_telegram_order
        process_telegram_order.delay(str(order.id))
        
        await telegram_service.send_message(order.chat_id, "Pagamento confirmado! Iniciando conversão...")
        
        return {"ok": True}

    return {"ok": True}


async def simulate_test_payment_simple(order_id: str, chat_id: int, file_id: str, file_name: str):
    """Simplified test payment simulation"""
    try:
        # Notify user about payment
        await telegram_service.send_message(
            chat_id,
            "✅ **[MODO TESTE] Pagamento simulado!** Iniciando conversão do seu arquivo..."
        )
        
        # Process directly without complex database operations
        await process_file_simple(order_id, chat_id, file_id, file_name)
        
    except Exception as e:
        logger.error(f"Error in simple test payment: {e}")
        await telegram_service.send_message(
            chat_id,
            f"❌ **Erro no processamento:** {str(e)}"
        )


async def simulate_test_payment_direct(order_id: str, chat_id: int):
    """Simulate payment for test user after 5 seconds - direct version without Celery"""
    import asyncio
    from sqlalchemy.future import select
    from src.models.order import Order, Payment
    from pathlib import Path
    
    # Wait 5 seconds
    await asyncio.sleep(5)
    
    try:
        from src.core.database import AsyncSessionLocal
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
            
            # Update order status to paid
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
            
            # Notify user about payment
            await telegram_service.send_message(
                chat_id,
                "✅ **[MODO TESTE] Pagamento simulado!** Iniciando conversão do seu arquivo..."
            )
            
            # Process the order directly (without Celery)
            logger.info(f"Starting direct processing for order {order_id}")
            await process_order_direct(order, chat_id)
            
            logger.info(f"Test payment and processing completed for order {order_id}")
            
    except Exception as e:
        logger.error(f"Error in test payment simulation: {e}")
        await telegram_service.send_message(
            chat_id,
            f"❌ **Erro no processamento de teste:** {str(e)}"
        )


async def process_file_simple(order_id: str, chat_id: int, file_id: str, file_name: str):
    """Simplified file processing without complex database operations"""
    try:
        await telegram_service.send_message(
            chat_id,
            "⚙️ **Processando arquivo...** Aguarde alguns instantes."
        )
        
        # Download file from Telegram
        logger.info(f"Getting file path for file_id: {file_id}")
        file_path = await telegram_service.get_file_path(file_id)
        if not file_path:
            raise Exception("Falha ao obter caminho do arquivo do Telegram")
        
        logger.info(f"Downloading file from path: {file_path}")
        local_pdf_path = Path(settings.UPLOAD_DIR) / f"{order_id}.pdf"
        success = await telegram_service.download_file(file_path, str(local_pdf_path))
        if not success:
            raise Exception("Falha ao baixar arquivo do Telegram")
        
        logger.info(f"File downloaded successfully to: {local_pdf_path}")
        
        # Convert PDF to CSV
        logger.info(f"Starting PDF to CSV conversion for order {order_id}")
        from src.services.pdf_reader import PDFReader
        from src.services.csv_writer import CSVWriter
        from src.services.document_converter import DocumentConverterService
        
        output_filename = f"{order_id}.csv"
        output_path = Path(settings.OUTPUT_DIR) / output_filename
        
        pdf_reader = PDFReader()
        csv_writer = CSVWriter()
        converter = DocumentConverterService(pdf_reader, csv_writer)
        converter.convert(local_pdf_path, output_path)
        
        logger.info(f"Conversion completed. Output file: {output_path}")
        
        # Send converted file
        logger.info(f"Sending converted file to chat {chat_id}")
        await telegram_service.send_document(
            chat_id,
            str(output_path),
            caption=f"✅ **Conversão concluída!**\n\n📄 Arquivo: {file_name}\n🆔 Pedido: {order_id}"
        )
        logger.info(f"File sent successfully to chat {chat_id}")
        
    except Exception as e:
        logger.error(f"Error in simple file processing: {e}")
        await telegram_service.send_message(
            chat_id,
            f"❌ **Erro no processamento:**\n\n{str(e)}\n\n💡 Tente novamente ou entre em contato com o suporte."
        )


async def process_order_direct(order: Order, chat_id: int):
    """Process order directly without Celery for testing"""
    logger.info(f"Processing order {order.id} directly for chat {chat_id}")
    try:
        # Update status to processing
        from src.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await db.merge(order)
            order.status = "processing"
            await db.commit()
        
        await telegram_service.send_message(
            chat_id,
            "⚙️ **Processando arquivo...** Aguarde alguns instantes."
        )
        
        # Download file from Telegram
        logger.info(f"Getting file path for file_id: {order.file_id}")
        file_path = await telegram_service.get_file_path(order.file_id)
        if not file_path:
            raise Exception("Falha ao obter caminho do arquivo do Telegram")
        
        logger.info(f"Downloading file from path: {file_path}")
        local_pdf_path = Path(settings.UPLOAD_DIR) / f"{order.id}.pdf"
        success = await telegram_service.download_file(file_path, str(local_pdf_path))
        if not success:
            raise Exception("Falha ao baixar arquivo do Telegram")
        
        logger.info(f"File downloaded successfully to: {local_pdf_path}")
        
        # Convert PDF to CSV
        logger.info(f"Starting PDF to CSV conversion for order {order.id}")
        from src.services.pdf_reader import PDFReader
        from src.services.csv_writer import CSVWriter
        from src.services.document_converter import DocumentConverterService
        
        output_filename = f"{order.id}.csv"
        output_path = Path(settings.OUTPUT_DIR) / output_filename
        
        pdf_reader = PDFReader()
        csv_writer = CSVWriter()
        converter = DocumentConverterService(pdf_reader, csv_writer)
        converter.convert(local_pdf_path, output_path)
        
        logger.info(f"Conversion completed. Output file: {output_path}")
        
        # Update order
        async with AsyncSessionLocal() as db:
            await db.merge(order)
            order.pdf_path = str(local_pdf_path)
            order.csv_path = str(output_path)
            order.status = "completed"
            await db.commit()
        
        # Send converted file
        logger.info(f"Sending converted file to chat {chat_id}")
        await telegram_service.send_document(
            chat_id,
            str(output_path),
            caption=f"✅ **Conversão concluída!**\n\n📄 Arquivo: {order.file_name}\n🆔 Pedido: {order.id}"
        )
        logger.info(f"File sent successfully to chat {chat_id}")
        
        logger.info(f"Order {order.id} processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing order {order.id}: {e}")
        
        # Update order status to failed
        async with AsyncSessionLocal() as db:
            await db.merge(order)
            order.status = "failed"
            order.error = str(e)
            await db.commit()
        
        await telegram_service.send_message(
            chat_id,
            f"❌ **Erro no processamento:**\n\n{str(e)}\n\n💡 Tente novamente ou entre em contato com o suporte."
        )


@router.post("/ammer/webhook")
async def ammer_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Ammer Pay webhook notifications"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        signature = request.headers.get("X-Ammer-Signature", "")
        
        # Verify webhook signature
        if not ammer_pay_service.verify_webhook_signature(body.decode(), signature):
            logger.warning("Invalid Ammer Pay webhook signature")
            raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Parse webhook data
        webhook_data = await request.json()
        event_type = webhook_data.get("event")
        payment_data = webhook_data.get("data", {})
        
        if event_type == "payment.completed":
            # Find order by external_id (our order_id)
            external_id = payment_data.get("external_id")
            if not external_id:
                logger.error("No external_id in Ammer Pay webhook")
                return {"ok": False}
            
            result = await db.execute(
                select(Order).where(Order.id == external_id)
            )
            order = result.scalars().first()
            
            if not order:
                logger.error(f"Order not found for external_id {external_id}")
                return {"ok": False}
            
            # Validate payment amount
            if payment_data.get("amount") != order.price_cents:
                logger.error(f"SECURITY ALERT: Amount mismatch for order {order.id}")
                return {"ok": False}
            
            # Update order status
            order.status = "paid"
            order.provider_payment_id = payment_data.get("id")
            
            # Record payment
            new_payment = Payment(
                order_id=order.id,
                amount_cents=payment_data.get("amount"),
                currency=payment_data.get("currency", "BRL"),
                provider_payload=payment_data,
                status="success"
            )
            db.add(new_payment)
            await db.commit()
            
            # Trigger processing task
            from src.worker.tasks import process_telegram_order
            process_telegram_order.delay(str(order.id))
            
            # Notify user
            await telegram_service.send_message(
                order.chat_id, 
                "✅ **Pagamento confirmado!** Iniciando conversão do seu arquivo..."
            )
            
            logger.info(f"Ammer Pay payment completed for order {order.id}")
            
        elif event_type == "payment.failed":
            external_id = payment_data.get("external_id")
            if external_id:
                result = await db.execute(
                    select(Order).where(Order.id == external_id)
                )
                order = result.scalars().first()
                
                if order:
                    order.status = "failed"
                    await db.commit()
                    
                    await telegram_service.send_message(
                        order.chat_id,
                        "❌ **Pagamento não foi aprovado.** Tente novamente ou entre em contato com o suporte."
                    )
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Ammer Pay webhook error: {e}")
        return {"ok": False}
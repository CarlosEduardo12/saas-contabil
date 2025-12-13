from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from src.core.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(Integer, nullable=False)
    file_id = Column(Text, nullable=False)
    file_name = Column(Text)
    file_size = Column(Integer)
    file_hash = Column(Text)
    price_cents = Column(Integer, nullable=False, default=5000)
    currency = Column(String(3), default='BRL')
    payload = Column(Text)
    status = Column(String(20), default='pending_payment')
    provider_payment_id = Column(Text)
    telegram_payment_id = Column(Text)
    
    # Ammer Pay fields
    ammer_payment_id = Column(Text)
    ammer_payment_url = Column(Text)
    payment_method = Column(String(20), default='ammer_pay')  # 'telegram' or 'ammer_pay'
    pdf_path = Column(Text)
    csv_path = Column(Text)
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    payments = relationship("Payment", back_populates="order")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    amount_cents = Column(Integer)
    currency = Column(String(3))
    provider_payload = Column(JSONB)
    status = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="payments")

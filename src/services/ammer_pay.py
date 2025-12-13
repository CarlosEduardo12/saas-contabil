import httpx
import hashlib
import hmac
import json
from typing import Dict, Any, Optional
from src.core.config import settings
from src.core.logging_config import logger


class AmmerPayService:
    """Service for Ammer Pay integration"""
    
    def __init__(self):
        self.api_key = settings.AMMER_PAY_API_KEY
        self.secret = settings.AMMER_PAY_SECRET
        self.base_url = "https://api.ammerpay.com/v1"
        
    def _generate_signature(self, data: str) -> str:
        """Generate HMAC signature for Ammer Pay"""
        return hmac.new(
            self.secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def create_payment_link(
        self,
        amount_cents: int,
        description: str,
        external_id: str,
        customer_name: str = "Cliente",
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a payment link with Ammer Pay
        
        Args:
            amount_cents: Amount in cents (R$ 50.00 = 5000)
            description: Payment description
            external_id: Your internal order ID
            customer_name: Customer name
            webhook_url: Webhook URL for payment notifications
            
        Returns:
            Dict with payment_url and payment_id
        """
        try:
            payload = {
                "amount": amount_cents,
                "currency": "BRL",
                "description": description,
                "external_id": external_id,
                "customer": {
                    "name": customer_name
                },
                "webhook_url": webhook_url,
                "expires_in": 3600  # 1 hour expiration
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/payments",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 201:
                    result = response.json()
                    logger.info(f"Ammer Pay link created for order {external_id}")
                    return {
                        "success": True,
                        "payment_url": result.get("payment_url"),
                        "payment_id": result.get("id"),
                        "qr_code": result.get("qr_code")
                    }
                else:
                    logger.error(f"Ammer Pay error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Payment service error: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Ammer Pay integration error: {e}")
            return {
                "success": False,
                "error": "Payment service temporarily unavailable"
            }
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get payment status from Ammer Pay"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/payments/{payment_id}",
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Ammer Pay status error: {response.status_code}")
                    return {"status": "unknown"}
                    
        except Exception as e:
            logger.error(f"Ammer Pay status check error: {e}")
            return {"status": "error"}
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature from Ammer Pay"""
        try:
            expected_signature = self._generate_signature(payload)
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Webhook signature verification error: {e}")
            return False
#!/usr/bin/env python3
"""
Test script for Ammer Pay integration
"""

import asyncio
import os
from src.services.ammer_pay import AmmerPayService
from src.core.config import settings

async def test_ammer_pay():
    """Test Ammer Pay service integration"""
    
    print("🧪 Testing Ammer Pay Integration...")
    print(f"API Key configured: {'Yes' if settings.AMMER_PAY_API_KEY else 'No'}")
    print(f"Secret configured: {'Yes' if settings.AMMER_PAY_SECRET else 'No'}")
    
    if not settings.AMMER_PAY_API_KEY or not settings.AMMER_PAY_SECRET:
        print("❌ Ammer Pay credentials not configured")
        print("Please set AMMER_PAY_API_KEY and AMMER_PAY_SECRET environment variables")
        return False
    
    service = AmmerPayService()
    
    # Test payment link creation
    print("\n🔗 Testing payment link creation...")
    result = await service.create_payment_link(
        amount_cents=5000,  # R$ 50.00
        description="Test PDF conversion",
        external_id="test-order-123",
        customer_name="Test Customer"
    )
    
    if result.get("success"):
        print("✅ Payment link created successfully!")
        print(f"Payment URL: {result.get('payment_url')}")
        print(f"Payment ID: {result.get('payment_id')}")
        
        # Test payment status check
        if result.get("payment_id"):
            print("\n📊 Testing payment status check...")
            status = await service.get_payment_status(result.get("payment_id"))
            print(f"Payment status: {status.get('status', 'unknown')}")
            
    else:
        print(f"❌ Payment link creation failed: {result.get('error')}")
        return False
    
    # Test webhook signature verification
    print("\n🔐 Testing webhook signature verification...")
    test_payload = '{"event":"payment.completed","data":{"id":"test"}}'
    signature = service._generate_signature(test_payload)
    
    if service.verify_webhook_signature(test_payload, signature):
        print("✅ Webhook signature verification working!")
    else:
        print("❌ Webhook signature verification failed!")
        return False
    
    print("\n🎉 All Ammer Pay tests passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_ammer_pay())
    
    if success:
        print("\n✅ Ammer Pay integration is ready!")
    else:
        print("\n❌ Ammer Pay integration has issues!")
        print("Please check your configuration and try again.")
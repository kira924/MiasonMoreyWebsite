import httpx
from fastapi import HTTPException, status
from app.core.config import settings
import hmac
import hashlib

class PaymobService:
    def __init__(self):
        # Retrieve keys from settings
        self.api_key = settings.PAYMOB_API_KEY
        self.card_integration_id = settings.PAYMOB_CARD_INTEGRATION_ID
        self.wallet_integration_id = settings.PAYMOB_WALLET_INTEGRATION_ID
        
        # Explicit headers to prevent WAF blocks
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def get_auth_token(self) -> str:
        """
        Step 1: Authenticate with Paymob and retrieve the transient Auth Token
        """
        # Hardcoded complete URL
        url = "https://accept.paymob.com/api/auth/tokens"
        payload = {"api_key": self.api_key}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            
        if response.status_code != 201:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to authenticate with Paymob: {response.text}"
            )
            
        return response.json().get("token")

    async def register_order(self, auth_token: str, amount_cents: int, merchant_order_id: str) -> int:
        """
        Step 2: Register the order on Paymob's servers
        """
        # Hardcoded complete URL
        url = "https://accept.paymob.com/api/ecommerce/orders"
        payload = {
            "auth_token": auth_token,
            "delivery_needed": "false",
            "amount_cents": amount_cents,
            "currency": "EGP",
            "merchant_order_id": merchant_order_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            
        if response.status_code != 201:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to register order on Paymob: {response.text}"
            )
            
        return response.json().get("id")

    async def get_payment_key(
        self, auth_token: str, paymob_order_id: int, amount_cents: int, user_info: dict, payment_method: str = "card"
    ) -> str:
        """
        Step 3: Generate the final Payment Key based on the selected payment method
        """
        # Hardcoded complete URL (Fixed the 'acceptance' path)
        url = "https://accept.paymob.com/api/acceptance/payment_keys"
        
        integration_id = self.wallet_integration_id if payment_method == "wallet" else self.card_integration_id

        payload = {
            "auth_token": auth_token,
            "amount_cents": amount_cents,
            "expiration": 3600,
            "order_id": paymob_order_id,
            "billing_data": {
                "apartment": "NA",
                "email": user_info.get("email", "test@example.com"),
                "floor": "NA",
                "first_name": user_info.get("full_name", "Customer").split()[0],
                "street": "NA",
                "building": "NA",
                "phone_number": user_info.get("phone_number", "+201000000000"),
                "shipping_method": "NA",
                "postal_code": "NA",
                "city": "NA",
                "country": "EG",
                "last_name": "NA"
            },
            "currency": "EGP",
            "integration_id": integration_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            
        if response.status_code != 201:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate Paymob payment key: {response.text}"
            )
            
        return response.json().get("token")
    
    async def process_wallet_payment(self, payment_key: str, phone_number: str) -> str:
            """
            Step 4 (Wallet Only): Send the wallet number to Paymob to get the redirect URL
            """
            url = "https://accept.paymob.com/api/acceptance/payments/pay"
            payload = {
                "source": {
                    "identifier": phone_number,
                    "subtype": "WALLET"
                },
                "payment_token": payment_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers)
                
            if response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to process wallet payment: {response.text}"
                )
                
            # Paymob returns a JSON containing a 'redirect_url' for wallets
            return response.json().get("redirect_url")
    
    def verify_webhook_mac(self, hmac_received: str, payload_obj: dict) -> bool:
        """
        Validates the HMAC sent by Paymob against the calculated HMAC from the payload.
        Paymob requires specific keys to be concatenated in a strict alphabetical order.
        """
        hmac_keys = [
            "amount_cents", "created_at", "currency", "error_occured",
            "has_parent_transaction", "id", "integration_id", "is_3d_secure",
            "is_auth", "is_capture", "is_refunded", "is_standalone_payment",
            "is_voided", "order.id", "owner", "pending", "source_data.pan",
            "source_data.sub_type", "source_data.type", "success"
        ]
        
        concatenated_string = ""
        
        for key in hmac_keys:
            if "." in key:
                parent_key, child_key = key.split(".")
                value = payload_obj.get(parent_key, {}).get(child_key, "")
            else:
                value = payload_obj.get(key, "")
                
            if isinstance(value, bool):
                value = str(value).lower()
                
            concatenated_string += str(value)
            
        calculated_hmac = hmac.new(
            settings.PAYMOB_HMAC_SECRET.encode("utf-8"),
            concatenated_string.encode("utf-8"),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(calculated_hmac, hmac_received)
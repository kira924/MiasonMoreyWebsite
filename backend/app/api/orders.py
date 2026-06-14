from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
import time

from app.core.database import get_db
from app.models.order import Order, OrderItem, OrderStatus
from app.models.cart import CartItem
from app.models.address import Address
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.api.deps import get_current_admin_user
from app.api.deps import get_current_active_user
from app.schemas.order import PaymentRequest
from app.services.paymob import PaymobService
from fastapi.responses import RedirectResponse

# Initialize the router for orders
router = APIRouter(
    prefix="/api/orders",
    tags=["Orders"]
)

# Initialize the payment service
paymob_service = PaymobService()

@router.post("/", response_model=OrderResponse)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Verify the address belongs to the user
    address = db.query(Address).filter(
        Address.id == order_in.address_id,
        Address.user_id == current_user.id
    ).first()
    
    if not address:
        raise HTTPException(status_code=404, detail="Address not found or does not belong to user")

    # Retrieve the user's cart items
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Calculate total price dynamically
    total_price = sum(item.quantity * item.product.price for item in cart_items)

    # Create the main order record
    new_order = Order(
        user_id=current_user.id,
        address_id=order_in.address_id,
        total_price=total_price,
        status=OrderStatus.PENDING
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Move items from cart to order items
    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            unit_price=cart_item.product.price # Lock in the current price
        )
        db.add(order_item)
        
    # Clear the user's cart after successful order creation
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    
    db.commit()
    db.refresh(new_order)
    
    return new_order

@router.get("/", response_model=List[OrderResponse])
def get_user_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Retrieve all orders for the current user, ordered by newest first
    return db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Retrieve a specific order ensuring it belongs to the current user
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    return order

@router.get("/admin/all", response_model=List[OrderResponse])
def get_all_orders_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Retrieve all orders in the store (Admin only)
    return db.query(Order).order_by(Order.created_at.desc()).all()

@router.patch("/admin/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    status_in: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Find the order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # Validate and update the status
    try:
        # This ensures the provided status is one of the valid Enum values
        order.status = OrderStatus(status_in.status)
    except ValueError:
        valid_statuses = [e.value for e in OrderStatus]
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid order status. Valid statuses are: {', '.join(valid_statuses)}"
        )
        
    db.commit()
    db.refresh(order)
    return order

@router.patch("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Retrieve the specific order ensuring it belongs to the current user
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # Prevent cancellation if the order has already been processed or shipped
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=400, 
            detail=f"Order cannot be cancelled because its current status is '{order.status}'"
        )
        
    # Update the status to cancelled
    order.status = OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    
    return order

@router.post("/{order_id}/pay")
async def process_payment(
    order_id: int,
    payment_in: PaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 1. Fetch the order from the database
    order = db.query(Order).filter(
        Order.id == order_id, 
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending orders can be paid for")

    # 2. Prepare data for Paymob
    amount_cents = int(order.total_price * 100) # Paymob deals in cents/piasters
    user_info = {
        "email": current_user.email,
        "full_name": current_user.full_name or "Customer",
        "phone_number": "01000000000" # In a real app, fetch from user's address
    }

    # 3. Execute the 3 steps of Paymob
    try:
        # Step A: Get Auth Token
        auth_token = await paymob_service.get_auth_token()
        
        # Step B: Register Order
        # Generate a unique string combining our order ID and the current timestamp
        unique_merchant_order_id = f"{order.id}_{int(time.time())}"
        
        paymob_order_id = await paymob_service.register_order(
            auth_token=auth_token, 
            amount_cents=amount_cents, 
            merchant_order_id=unique_merchant_order_id 
        )
        
        # Step C: Get Payment Key
        payment_key = await paymob_service.get_payment_key(
            auth_token=auth_token,
            paymob_order_id=paymob_order_id,
            amount_cents=amount_cents,
            user_info=user_info,
            payment_method=payment_in.payment_method
        )
        
        # 4. Generate the final URL for the frontend to redirect the user
        if payment_in.payment_method == "wallet":
            # For wallets, make an additional request to get the redirect link
            # Note: In a real scenario, extract the phone number from the user's address profile
            test_wallet_number = "01010101010" 
            payment_url = await paymob_service.process_wallet_payment(
                payment_key=payment_key,
                phone_number=test_wallet_number
            )
        else:
            # For cards, you will need an Iframe ID from your Paymob dashboard
            # Replace 'YOUR_IFRAME_ID' with the actual iframe ID from Paymob
            payment_url = f"https://accept.paymob.com/api/acceptance/iframes/1052881?payment_token={payment_key}"
            
        return {
            "payment_key": payment_key,
            "payment_url": payment_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")
    
@router.post("/webhook/paymob")
async def paymob_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    # 1. Get the HMAC from the query parameters sent by Paymob
    hmac_received = request.query_params.get("hmac")
    
    if not hmac_received:
        raise HTTPException(status_code=401, detail="Missing HMAC parameter")

    # 2. Get the JSON payload
    payload = await request.json()
    obj = payload.get("obj", {})
    
    # 3. Validate the HMAC signature to ensure the request is authentically from Paymob
    if not paymob_service.verify_webhook_mac(hmac_received, obj):
        raise HTTPException(status_code=401, detail="Invalid HMAC signature")
    
    # 4. Check if the event type is a transaction callback
    if payload.get("type") == "TRANSACTION":
        success = obj.get("success", False)
        merchant_order_id = obj.get("order", {}).get("merchant_order_id", "")
        
        try:
            actual_order_id_str = merchant_order_id.split("_")[0]
            order_id = int(actual_order_id_str)
        except (ValueError, IndexError):
            return {"status": "ignored", "reason": "Invalid merchant_order_id format"}
            
        order = db.query(Order).filter(Order.id == order_id).first()
        
        # ... inside the webhook, after finding the order ...
        if order:
            if success:
                try:
                    # 1. Update order status to PROCESSING
                    order.status = OrderStatus.PROCESSING 
                    
                    # 2. Deduct inventory with Row-Level Locking to prevent race conditions
                    for order_item in order.items:
                        # Lock the specific product row until this transaction is committed or rolled back
                        product = db.query(Product).with_for_update().filter(Product.id == order_item.product_id).first()
                        
                        if product:
                            if product.stock >= order_item.quantity:
                                product.stock -= order_item.quantity
                            else:
                                # Handle out of stock scenario gracefully
                                product.stock = 0 
                                
                    # 3. Clear the user's cart
                    db.query(CartItem).filter(CartItem.user_id == order.user_id).delete()
                    
                    # 4. Commit the transaction (All operations succeed together)
                    db.commit()
                    
                except Exception as e:
                    # 5. Rollback the transaction if any error occurs (All operations fail together)
                    db.rollback()
                    # You should log the exception 'e' here using your logger
            else:
                try:
                    order.status = OrderStatus.FAILED
                    db.commit()
                except Exception as e:
                    db.rollback()
                
    return {"status": "success"}

@router.get("/payment/callback")
async def payment_response_callback(request: Request):
    # Paymob sends the transaction result as query parameters in the URL
    query_params = request.query_params
    success = query_params.get("success")
    merchant_order_id = query_params.get("merchant_order_id", "")
    
    # Extract our original order ID
    order_id = merchant_order_id.split("_")[0] if "_" in merchant_order_id else merchant_order_id
    
    # Define your frontend URLs (Assuming your frontend runs on port 3000 locally)
    # In production, this will be your actual domain (e.g., https://miasonmorey.com)
    frontend_base_url = "http://localhost:3000"
    
    if success == "true":
        # Redirect the user to the success page on your frontend
        redirect_url = f"{frontend_base_url}/payment-success?order_id={order_id}"
    else:
        # Redirect the user to the failure page on your frontend
        redirect_url = f"{frontend_base_url}/payment-failed?order_id={order_id}"
        
    return RedirectResponse(url=redirect_url)
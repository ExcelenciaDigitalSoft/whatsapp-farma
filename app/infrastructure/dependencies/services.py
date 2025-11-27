"""Service dependency providers for FastAPI."""
from typing import Annotated
from fastapi import Depends

# This file will be populated with service dependencies as we implement them
# Example pattern:
#
# from app.domain.interfaces.services import IPaymentGateway
# from app.infrastructure.external.payment import MercadoPagoAdapter
# from app.infrastructure.config import get_settings
#
# def get_payment_gateway() -> IPaymentGateway:
#     """Provide payment gateway implementation."""
#     settings = get_settings()
#     return MercadoPagoAdapter(
#         access_token=settings.payment.mercadopago_access_token,
#         public_key=settings.payment.mercadopago_public_key
#     )
#
# PaymentGatewayDep = Annotated[IPaymentGateway, Depends(get_payment_gateway)]

# This approach follows Dependency Inversion Principle:
# - High-level modules (use cases) depend on abstractions (interfaces)
# - Low-level modules (adapters) implement abstractions
# - Dependency injection wires them together at runtime

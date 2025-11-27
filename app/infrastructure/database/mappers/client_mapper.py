"""Mapper between Client entity and SQLAlchemy model."""
from app.domain.entities import Client
from app.domain.value_objects import Phone, Email, Address, TaxId, Money, ClientBalance
from app.models.client import Client as ClientModel


class ClientMapper:
    """
    Maps between Client domain entity and ClientModel (SQLAlchemy).

    Handles the translation between the rich domain model and the
    persistence model, preserving all business logic in the domain layer.
    """

    @staticmethod
    def to_model(entity: Client) -> ClientModel:
        """
        Convert domain entity to SQLAlchemy model.

        Args:
            entity: Client domain entity

        Returns:
            ClientModel for persistence
        """
        return ClientModel(
            id=entity.id,
            pharmacy_id=entity.pharmacy_id,
            external_id=entity.external_id,
            phone=entity.phone.value,
            phone_normalized=entity.phone.normalized,
            first_name=entity.first_name,
            last_name=entity.last_name,
            full_name=entity.full_name,
            email=str(entity.email) if entity.email else None,
            tax_id=str(entity.tax_id) if entity.tax_id else None,
            address=entity.address.street if entity.address else None,
            city=entity.address.city if entity.address else None,
            state=entity.address.state if entity.address else None,
            postal_code=entity.address.postal_code if entity.address else None,
            whatsapp_name=entity.whatsapp_name,
            whatsapp_opted_in=entity.whatsapp_opted_in,
            last_whatsapp_interaction=entity.last_whatsapp_interaction,
            credit_limit=entity.balance.credit_limit.amount,
            current_balance=entity.balance.current_balance.amount,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
            tags=entity.tags,
            notes=entity.notes,
        )

    @staticmethod
    def to_entity(model: ClientModel) -> Client:
        """
        Convert SQLAlchemy model to domain entity.

        Args:
            model: ClientModel from database

        Returns:
            Client domain entity
        """
        # Create value objects
        phone = Phone.from_normalized(model.phone_normalized)

        email = None
        if model.email:
            email = Email.create(model.email)

        tax_id = None
        if model.tax_id:
            tax_id = TaxId.create(model.tax_id)

        address = Address.create(
            street=model.address,
            city=model.city,
            state=model.state,
            postal_code=model.postal_code,
            country="AR"
        )

        # Create balance
        credit_limit = Money.create(model.credit_limit, "ARS")
        current_balance = Money.create(model.current_balance, "ARS")
        balance = ClientBalance.create(current_balance, credit_limit)

        # Create entity
        client = Client(
            pharmacy_id=model.pharmacy_id,
            phone=phone,
            balance=balance,
            status=model.status,
            first_name=model.first_name,
            last_name=model.last_name,
            email=email,
            tax_id=tax_id,
            address=address,
            whatsapp_name=model.whatsapp_name,
            whatsapp_opted_in=model.whatsapp_opted_in,
            last_whatsapp_interaction=model.last_whatsapp_interaction,
            tags=model.tags or [],
            notes=model.notes,
            external_id=model.external_id,
        )

        # Set timestamps and ID from database
        client.id = model.id
        client.created_at = model.created_at
        client.updated_at = model.updated_at
        client.deleted_at = model.deleted_at

        return client

    @staticmethod
    def update_model_from_entity(model: ClientModel, entity: Client) -> None:
        """
        Update existing SQLAlchemy model with entity data.

        Args:
            model: Existing ClientModel to update
            entity: Client entity with new data
        """
        model.pharmacy_id = entity.pharmacy_id
        model.external_id = entity.external_id
        model.phone = entity.phone.value
        model.phone_normalized = entity.phone.normalized
        model.first_name = entity.first_name
        model.last_name = entity.last_name
        model.full_name = entity.full_name
        model.email = str(entity.email) if entity.email else None
        model.tax_id = str(entity.tax_id) if entity.tax_id else None
        model.address = entity.address.street if entity.address else None
        model.city = entity.address.city if entity.address else None
        model.state = entity.address.state if entity.address else None
        model.postal_code = entity.address.postal_code if entity.address else None
        model.whatsapp_name = entity.whatsapp_name
        model.whatsapp_opted_in = entity.whatsapp_opted_in
        model.last_whatsapp_interaction = entity.last_whatsapp_interaction
        model.credit_limit = entity.balance.credit_limit.amount
        model.current_balance = entity.balance.current_balance.amount
        model.status = entity.status
        model.updated_at = entity.updated_at
        model.deleted_at = entity.deleted_at
        model.tags = entity.tags
        model.notes = entity.notes

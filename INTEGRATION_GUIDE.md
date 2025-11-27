# Guía de Integración - Arquitectura Clean

## Integración en main.py

Para integrar los nuevos endpoints de Clean Architecture en tu aplicación FastAPI:

### 1. Actualizar main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importar configuración segregada
from app.infrastructure.config import get_settings

# Importar nuevo router de Clean Architecture
from app.presentation.api.router import api_router

# Importar routers legacy (opcional, durante migración)
# from app.api.routes import router as legacy_router

# Crear aplicación
settings = get_settings()
app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    description=settings.app.description,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.allowed_origins,
    allow_credentials=settings.security.allow_credentials,
    allow_methods=settings.security.allowed_methods,
    allow_headers=settings.security.allowed_headers,
)

# Incluir routers de Clean Architecture
app.include_router(api_router)

# (Opcional) Mantener endpoints legacy durante migración
# app.include_router(legacy_router, prefix="/api/legacy")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.app.environment,
        "version": settings.app.version,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.reload,
    )
```

### 2. Estructura de Requests

#### Crear Cliente

```bash
POST /api/v1/clients
Content-Type: application/json

{
  "pharmacy_id": "uuid-here",
  "phone": "+54 9 11 1234 5678",
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "juan@example.com",
  "credit_limit": 5000.00,
  "tags": ["vip", "mayorista"]
}
```

**Response:**

```json
{
  "id": "client-uuid",
  "pharmacy_id": "pharmacy-uuid",
  "phone": "+54 9 11 1234 5678",
  "phone_normalized": "5491112345678",
  "first_name": "Juan",
  "last_name": "Pérez",
  "full_name": "Juan Pérez",
  "email": "juan@example.com",
  "credit_limit": 5000.00,
  "current_balance": 0.00,
  "available_credit": 5000.00,
  "owes_money": false,
  "status": "active",
  "whatsapp_opted_in": true,
  "tags": ["vip", "mayorista"]
}
```

#### Obtener Cliente

```bash
GET /api/v1/clients/{client_id}
```

### 3. Manejo de Errores

Los endpoints retornan errores HTTP estándar:

- **400 Bad Request**: Errores de validación o reglas de negocio
- **404 Not Found**: Entidad no encontrada
- **500 Internal Server Error**: Errores del servidor

Ejemplo de error:

```json
{
  "detail": "Client with phone='+54 9 11 1234 5678' already exists"
}
```

### 4. Beneficios de la Nueva Arquitectura

✅ **Inyección de Dependencias Automática**
- FastAPI maneja toda la inyección mediante `Depends()`
- No necesitas instanciar manualmente repositorios o use cases

✅ **Validación Type-Safe**
- Pydantic valida requests automáticamente
- Domain valida reglas de negocio

✅ **Testabilidad Perfecta**
```python
# Test example
async def test_create_client():
    # Mock use case
    mock_use_case = Mock(spec=CreateClientUseCase)
    mock_use_case.execute.return_value = client_dto

    # Inject mock
    response = await create_client(request, use_case=mock_use_case)

    assert response.id == expected_id
```

✅ **Separación de Capas**
- Presentation: Validación HTTP, serialización
- Application: Orquestación, use cases
- Domain: Reglas de negocio puras
- Infrastructure: Persistencia, APIs externas

### 5. Migración Gradual

Puedes mantener los endpoints legacy y nuevos simultáneamente:

```python
# Legacy endpoints
app.include_router(legacy_router, prefix="/api/legacy/v1")

# New Clean Architecture endpoints
app.include_router(api_router, prefix="/api/v1")
```

Esto permite migrar gradualmente sin romper clientes existentes.

### 6. Próximos Pasos

1. **Migrar más endpoints**: Transactions, Payments, etc.
2. **Implementar TransactionRepository**: Completar infraestructura
3. **Agregar middleware de autenticación**: Integrar con use cases
4. **Implementar tests**: Unit, integration, E2E
5. **Documentación automática**: OpenAPI/Swagger ya incluido

## Comandos Útiles

```bash
# Iniciar servidor
poetry run start

# Ejecutar tests
poetry run test

# Linting
poetry run lint

# Format code
poetry run format

# Type checking
poetry run typecheck

# All quality checks
poetry run quality
```

## Estructura Final

```
app/
├── domain/              # ✅ Lógica de negocio pura
├── application/         # ✅ Casos de uso
├── infrastructure/      # ✅ Repositorios, adapters
└── presentation/        # ✅ API endpoints (nuevo)
    └── api/
        ├── router.py    # Router principal
        └── v1/
            └── clients.py  # Endpoints de clientes
```

Esta arquitectura está lista para escalar! 🚀

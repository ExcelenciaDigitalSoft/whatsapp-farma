# WhatsApp Pharmacy Assistant

Sistema de cobro y gestión de pagos para farmacias a través de WhatsApp, con integración a Mercado Pago. Implementado con **Clean Architecture** siguiendo principios SOLID y Domain-Driven Design (DDD).

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118+-green.svg)](https://fastapi.tiangolo.com)
[![Poetry](https://img.shields.io/badge/Poetry-managed-blue.svg)](https://python-poetry.org/)
[![Tests](https://img.shields.io/badge/tests-147%20passing-brightgreen.svg)](tests/)
[![Code Coverage](https://img.shields.io/badge/coverage-13.27%25-yellow.svg)](htmlcov/)

## 🎯 Características

### Core Features
- ✅ **Multi-tenant**: Soporte para múltiples farmacias con aislamiento de datos
- ✅ **Clean Architecture**: Separación completa de capas (Domain, Application, Infrastructure, Presentation)
- ✅ **Type-Safe**: Value Objects inmutables con validaciones estrictas
- ✅ **Testeable**: 147 tests comprehensivos (unit, integration, E2E)
- ✅ **SOLID Principles**: Inversión de dependencias y alta cohesión

### Business Features
- 💰 **Gestión de Clientes**: CRUD completo con límites de crédito y balance
- 📄 **Transacciones**: Facturas, pagos, notas de crédito/débito
- 💳 **Mercado Pago**: Generación de links de pago y procesamiento de webhooks
- 📱 **WhatsApp**: Integración vía Chattigo API con notificaciones
- 🔐 **Autenticación**: Sistema de tokens con roles y permisos (RBAC)
- 📊 **Auditoría**: Registro completo de operaciones

### Technical Stack
- 🐍 **Python 3.11+** - Async/await nativo
- ⚡ **FastAPI** - Framework web moderno y rápido
- 🗄️ **PostgreSQL** - Base de datos principal (transacciones)
- 🍃 **MongoDB** - Historial de chat
- 🔴 **Redis** - Cache y rate limiting
- 📦 **Poetry** - Gestión de dependencias
- 🧪 **pytest** - Testing framework
- 🔧 **Alembic** - Migraciones de base de datos

## 🏗️ Clean Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│              (FastAPI Endpoints, Schemas)                │
│                    app/presentation/                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Application Layer                       │
│          (Use Cases, DTOs, Orchestration)                │
│                   app/application/                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    Domain Layer                          │
│    (Entities, Value Objects, Domain Services)            │
│                     app/domain/                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  - Client, Pharmacy, Transaction (Entities)       │  │
│  │  - Phone, Money, ClientBalance (Value Objects)    │  │
│  │  - TransactionNumberGenerator (Domain Service)    │  │
│  │  - IClientRepository (Interface)                  │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                Infrastructure Layer                      │
│     (Repositories, Adapters, External Services)          │
│                 app/infrastructure/                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │  - ClientRepository (SQLAlchemy)                  │  │
│  │  - ChattigoAdapter (WhatsApp)                     │  │
│  │  - MercadoPagoAdapter (Payments)                  │  │
│  │  - DependencyContainer (DI)                       │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Principios Aplicados

✅ **Dependency Inversion**: Domain no depende de Infrastructure
✅ **Interface Segregation**: Interfaces específicas por caso de uso
✅ **Single Responsibility**: Una razón para cambiar por clase
✅ **Open/Closed**: Abierto para extensión, cerrado para modificación
✅ **Liskov Substitution**: Abstracciones intercambiables

## 📁 Estructura del Proyecto

```
whatsapp-pharmacy-assistant/
├── app/
│   ├── domain/                      # ⭐ Capa de Dominio (Puro)
│   │   ├── entities/               # Entidades de negocio
│   │   │   ├── base.py             # BaseEntity con timestamps
│   │   │   ├── client.py           # Cliente (reglas de negocio)
│   │   │   ├── pharmacy.py         # Farmacia (multi-tenant)
│   │   │   └── transaction.py      # Transacción financiera
│   │   ├── value_objects/          # Objetos de valor inmutables
│   │   │   ├── phone.py            # Teléfono con normalización E.164
│   │   │   ├── money.py            # Dinero con aritmética decimal
│   │   │   ├── client_balance.py   # Balance y crédito disponible
│   │   │   ├── address.py          # Dirección postal
│   │   │   ├── email.py            # Email validado
│   │   │   └── tax_id.py           # DNI/CUIT/CUIL validado
│   │   ├── services/               # Servicios de dominio
│   │   │   ├── client_validator.py # Validaciones de cliente
│   │   │   └── transaction_number_generator.py
│   │   ├── interfaces/             # Contratos (Ports)
│   │   │   ├── repositories/       # Repository interfaces
│   │   │   └── services/           # Service interfaces
│   │   └── exceptions/             # Excepciones de dominio
│   │
│   ├── application/                 # ⚙️ Capa de Aplicación
│   │   ├── use_cases/              # Casos de uso (CQRS)
│   │   │   ├── create_client.py    # Crear cliente
│   │   │   ├── get_client.py       # Consultar cliente
│   │   │   ├── create_transaction.py
│   │   │   └── process_payment.py
│   │   ├── dto/                    # Data Transfer Objects
│   │   │   ├── client_dto.py
│   │   │   └── transaction_dto.py
│   │   └── interfaces/             # Use case interfaces
│   │
│   ├── infrastructure/              # 🔧 Capa de Infraestructura
│   │   ├── database/
│   │   │   ├── models/             # SQLAlchemy models
│   │   │   ├── repositories/       # Repository implementations
│   │   │   └── mappers/            # Entity ↔ Model mappers
│   │   ├── external/               # Adaptadores externos
│   │   │   ├── whatsapp/           # ChattigoAdapter
│   │   │   └── payment/            # MercadoPagoAdapter
│   │   ├── config/                 # Configuración segregada
│   │   │   ├── application.py      # App settings
│   │   │   ├── database.py         # DB config
│   │   │   ├── whatsapp.py         # WhatsApp config
│   │   │   ├── payment.py          # Payment config
│   │   │   ├── security.py         # Security config
│   │   │   └── settings.py         # Unified settings
│   │   └── dependencies/           # Dependency Injection
│   │       ├── container.py        # DI Container
│   │       ├── database.py         # DB dependencies
│   │       └── use_cases.py        # Use case providers
│   │
│   ├── presentation/                # 🌐 Capa de Presentación
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   └── clients.py      # Client endpoints
│   │   │   └── router.py           # Main API router
│   │   └── schemas/                # Pydantic request/response
│   │
│   ├── middleware/                  # Middleware (auth, errors)
│   ├── api/                        # Legacy endpoints (migración gradual)
│   └── main.py                     # FastAPI application
│
├── tests/                           # 🧪 Test Suite (147 tests)
│   ├── unit/                       # Unit tests (fast, isolated)
│   │   ├── domain/
│   │   │   ├── value_objects/      # 106 tests (Phone, Money, Balance)
│   │   │   ├── entities/           # 16 tests (Client)
│   │   │   └── services/           # 28 tests (Validators, Generators)
│   │   └── application/
│   │       └── use_cases/          # 11 tests (CreateClient con mocks)
│   ├── integration/                # Integration tests (database)
│   │   └── repositories/           # 16 tests (ClientRepository)
│   ├── e2e/                        # End-to-end tests (HTTP)
│   │   └── api/                    # 15 tests (API endpoints)
│   ├── conftest.py                 # Shared fixtures
│   └── README.md                   # Testing documentation
│
├── alembic/                         # Database migrations
├── scripts/                         # Utility scripts
│   └── setup-quality-tools.sh      # Pre-commit setup
├── docker-compose.yml               # PostgreSQL + MongoDB + Redis
├── pyproject.toml                   # Poetry configuration
├── .pre-commit-config.yaml          # Code quality hooks
├── INTEGRATION_GUIDE.md             # Clean Architecture integration guide
└── README.md                        # This file
```

## 🚀 Inicio Rápido

### 1. Prerequisitos

- Python 3.11 o superior
- Poetry (gestor de dependencias)
- Docker & Docker Compose (para bases de datos)

```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Verificar instalación
poetry --version
```

### 2. Clonar y Configurar

```bash
# Clonar repositorio
git clone https://github.com/Excelencia-Digital-Soft/whatsapp-pharmacy-assistant.git
cd whatsapp-pharmacy-assistant

# Copiar variables de entorno
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

### 3. Instalar Dependencias

```bash
# Instalar todas las dependencias (incluye dev y test)
poetry install

# Solo dependencias de producción
poetry install --only main

# Activar entorno virtual
poetry shell
```

### 4. Iniciar Servicios (Docker)

```bash
# Iniciar PostgreSQL, MongoDB y Redis
docker-compose up -d

# Verificar servicios
docker-compose ps

# Ver logs
docker-compose logs -f
```

### 5. Ejecutar Migraciones

```bash
# Generar migración inicial
poetry run alembic revision --autogenerate -m "Initial schema"

# Aplicar migraciones
poetry run alembic upgrade head

# Ver estado de migraciones
poetry run alembic current
```

### 6. Iniciar Aplicación

```bash
# Modo desarrollo con auto-reload
poetry run uvicorn app.main:app --reload --port 3019

# Acceder a documentación interactiva
open http://localhost:3019/docs
```

## 📡 API Endpoints (Clean Architecture)

### Health Check

```bash
GET /health
Response: {
  "status": "healthy",
  "environment": "development",
  "version": "0.1.0"
}
```

### Clientes (Clean Architecture)

```bash
# Crear cliente
POST /api/v1/clients
Headers: Authorization: Bearer {token}
Body: {
  "pharmacy_id": "uuid",
  "phone": "+54 9 11 1234 5678",
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "juan@example.com",
  "credit_limit": 5000.00,
  "tags": ["vip", "mayorista"]
}
Response: {
  "id": "uuid",
  "phone": "+54 9 11 1234 5678",
  "phone_normalized": "+5491112345678",
  "first_name": "Juan",
  "last_name": "Pérez",
  "full_name": "Juan Pérez",
  "credit_limit": 5000.00,
  "current_balance": 0.00,
  "available_credit": 5000.00,
  "owes_money": false,
  "status": "active"
}

# Obtener cliente por ID
GET /api/v1/clients/{client_id}
Headers: Authorization: Bearer {token}
```

Ver `INTEGRATION_GUIDE.md` para más detalles sobre la integración de endpoints.

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
poetry run pytest

# Tests unitarios (rápidos)
poetry run pytest tests/unit/

# Tests de integración
poetry run pytest tests/integration/

# Tests E2E
poetry run pytest tests/e2e/

# Con cobertura
poetry run pytest --cov=app --cov-report=html --cov-report=term

# Ver reporte de cobertura
open htmlcov/index.html
```

### Test Suite

| Tipo | Cantidad | Cobertura | Descripción |
|------|----------|-----------|-------------|
| **Unit - Value Objects** | 106 | ~45% | Phone, Money, ClientBalance, Address, Email, TaxId |
| **Unit - Entities** | 16 | ~43% | Client, Pharmacy, Transaction |
| **Unit - Services** | 28 | 100% | Validators, Generators |
| **Unit - Use Cases** | 11 | 100% | Con mocks |
| **Integration** | 16 | 80% | Repositories con SQLite |
| **E2E** | 15 | 75% | API endpoints |
| **TOTAL** | **147** | **13.27%** | Overall (bajo por infraestructura pendiente) |

Ver `tests/README.md` para documentación completa de testing.

## 🔧 Herramientas de Calidad

### Pre-commit Hooks

```bash
# Instalar pre-commit hooks
poetry run pre-commit install

# Ejecutar manualmente en todos los archivos
poetry run pre-commit run --all-files

# O usar el script de configuración
chmod +x scripts/setup-quality-tools.sh
./scripts/setup-quality-tools.sh
```

### Herramientas Configuradas

- ✅ **Black** - Formateo automático de código
- ✅ **Ruff** - Linting ultra-rápido (reemplaza flake8 + pylint)
- ✅ **isort** - Ordenamiento de imports
- ✅ **mypy** - Type checking estático
- ✅ **Bandit** - Análisis de seguridad
- ✅ **Hadolint** - Linting de Dockerfile
- ✅ **Prettier** - Formateo de YAML/JSON
- ✅ **Interrogate** - Cobertura de docstrings

### Comandos de Calidad

```bash
# Linting
poetry run ruff check .
poetry run ruff check --fix .

# Formateo
poetry run black .
poetry run black --check .

# Type checking
poetry run mypy app/

# Análisis de seguridad
poetry run bandit -r app/

# Todo junto (calidad completa)
poetry run pre-commit run --all-files
```

## 📦 Deployment

### Docker

```bash
# Build imagen
docker-compose build app

# Ejecutar aplicación
docker-compose up -d

# Ver logs
docker-compose logs -f app

# Detener servicios
docker-compose down
```

### Variables de Entorno (Producción)

```bash
# App Configuration
ENVIRONMENT=production
DEBUG=false
APP_NAME="WhatsApp Pharmacy Assistant"
APP_VERSION="0.1.0"
HOST=0.0.0.0
PORT=3019

# Security
SECRET_KEY=<random-256-bit-key>
JWT_SECRET_KEY=<random-256-bit-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/pharmacy_db
MONGODB_URL=mongodb://user:pass@host:27017/pharmacy_chat
REDIS_URL=redis://host:6379/0

# External Services
MERCADOPAGO_ACCESS_TOKEN=<production-token>
MERCADOPAGO_PUBLIC_KEY=<public-key>
CHATTIGO_API_URL=https://api.chattigo.com
CHATTIGO_AUTH_TOKEN=<production-token>
CHATTIGO_WHATSAPP_NUMBER=+5491112345678

# CORS
ALLOWED_ORIGINS=["https://app.farmacia.com", "https://admin.farmacia.com"]
```

## 🎯 Arquitectura: Beneficios

### 1. Testabilidad
- ✅ **95%+ testeable**: Domain y Application completamente testeables
- ✅ **Mocks sencillos**: Interfaces claras para mocking
- ✅ **Tests rápidos**: Unit tests en milisegundos

### 2. Mantenibilidad
- ✅ **Separación clara**: Cada capa tiene una responsabilidad única
- ✅ **Bajo acoplamiento**: Cambios aislados por capa
- ✅ **Alta cohesión**: Código relacionado agrupado

### 3. Escalabilidad
- ✅ **Fácil extensión**: Nuevos use cases sin modificar existentes
- ✅ **Swap de implementaciones**: Cambiar repositorios o adapters sin tocar domain
- ✅ **Multi-tenant**: Aislamiento por farmacia

### 4. Desarrollo en Equipo
- ✅ **Contratos claros**: Interfaces bien definidas
- ✅ **Parallel development**: Capas independientes
- ✅ **Onboarding rápido**: Estructura predecible

## 📚 Documentación Adicional

- 📖 [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - Guía de integración de Clean Architecture
- 🧪 [tests/README.md](tests/README.md) - Documentación completa de testing
- 🔧 [.pre-commit-config.yaml](.pre-commit-config.yaml) - Configuración de quality hooks

## 🛣️ Roadmap

### Completado ✅
- [x] Clean Architecture implementation
- [x] Domain layer (Value Objects, Entities, Services)
- [x] Application layer (Use Cases, DTOs)
- [x] Infrastructure layer (Repositories, Adapters)
- [x] Presentation layer (API Endpoints)
- [x] Comprehensive test suite (147 tests)
- [x] Pre-commit hooks and quality tools

### En Progreso 🚧
- [ ] Implementar SQLAlchemy models completos
- [ ] Migrar todos los endpoints a Clean Architecture
- [ ] Tests de integración para todos los repositorios
- [ ] Tests E2E para todos los endpoints
- [ ] Documentación OpenAPI/Swagger completa

### Planeado 📋
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring y logging (Prometheus + Grafana)
- [ ] Rate limiting avanzado
- [ ] Caching con Redis
- [ ] Autenticación OAuth2
- [ ] Multi-language support
- [ ] PDF generation para facturas
- [ ] WhatsApp chatbot con IA

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Asegurar que los tests pasen (`poetry run pytest`)
4. Asegurar que pre-commit pase (`poetry run pre-commit run --all-files`)
5. Commit cambios (`git commit -m 'feat: agregar nueva funcionalidad'`)
6. Push a la rama (`git push origin feature/nueva-funcionalidad`)
7. Abrir Pull Request

### Convenciones de Commits

```
feat: nueva funcionalidad
fix: corrección de bug
docs: cambios en documentación
style: formateo, espacios, etc.
refactor: refactorización de código
test: agregar o modificar tests
chore: tareas de mantenimiento
```

## 📝 Licencia

**Copyright © 2025 Excelencia Digital Software**

Este proyecto es **confidencial y de uso exclusivo** de Excelencia Digital Software y sus clientes autorizados.

### Derechos Reservados

Todos los derechos reservados. Este software y su documentación son propiedad de **Excelencia Digital Software** y están protegidos por las leyes de derechos de autor y tratados internacionales.

### Confidencialidad

⚠️ **CONFIDENCIAL** - Este código fuente contiene información propietaria y confidencial. No está permitido:

- ❌ Copiar, modificar o distribuir el código sin autorización expresa
- ❌ Divulgar información del sistema a terceros no autorizados
- ❌ Usar el código para proyectos ajenos a los autorizados por Excelencia
- ❌ Hacer ingeniería inversa o decompilar componentes del sistema

### Uso Autorizado

✅ El uso de este software está limitado a:
- Personal autorizado de Excelencia Digital Software
- Clientes con licencia vigente y acuerdo de confidencialidad
- Ambientes de desarrollo, testing y producción autorizados

Para consultas sobre licenciamiento o uso del software, contactar:
- 📧 Email: support@excelenciasoftware.com.ar
- 🌐 Web: excelenciadigital.net

## 🆘 Soporte

- 📧 Email: support@excelenciasoftware.com.ar
- 🐛 Issues: [GitHub Issues](https://github.com/Excelencia-Digital-Soft/whatsapp-pharmacy-assistant/issues)
- 📖 Docs: Ver archivos en este repositorio

---

**Desarrollado con ❤️ por Excelencia**

*Powered by Clean Architecture, Domain-Driven Design, and SOLID Principles*

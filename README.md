# ZidShip Courier Framework

## 🚀 Overview
A unified courier integration framework designed for ZidShip to abstract 35+ courier integrations behind a single, consistent interface. Built with Django and Django REST Framework.

## 🏗️ Architecture & Trade-offs

### Hexagonal Architecture (Ports & Adapters)
We chose a Hexagonal architecture to decouple the core business logic (`ShipmentService`) from the external courier implementations.
- **Port**: `CourierBase` abstract class defining the interface.
- **Adapters**: `SMSACourier`, `MockCourier`.

### Trade-offs
1.  **JSONB vs Normalized Tables**:
    -   *Decision*: Use `JSONField` (JSONB in Postgres) for courier-specific data.
    -   *Reason*: Couriers have highly variable metadata. Normalizing every field would lead to an unmaintainable schema (EAV pattern). JSONB gives us flexibility with query performance.
2.  **Synchronous API**:
    -   *Decision*: Keep `create_shipment` synchronous for now.
    -   *Reason*: Simplicity for the MVP. In a high-scale production environment, we would offload the actual API calls to Celery tasks to prevent request blocking.
3.  **Code-based Configuration**:
    -   *Decision*: `CourierFactory` registry.
    -   *Reason*: Easier to unit test and maintain than database-stored configuration for behaviors, though API keys are loaded from settings/env.

## 🛠️ Features
- **Unified Interface**: Create, Track, Cancel, Print Label.
- **REST API**: Fully documented with Swagger/OpenAPI.
- **Retries**: Robust HTTP client with exponential backoff retries.
- **Mock Mode**: Functionality enabled without real API keys.

## 📦 Setup

1.  **Install**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Migrate**:
    ```bash
    python manage.py migrate
    ```

3.  **Run**:
    ```bash
    python manage.py runserver
    ```

## 🧪 Testing

- **Unit Tests**: `python manage.py test core`
- **Integration Scenario**: `python manage.py test_integration`

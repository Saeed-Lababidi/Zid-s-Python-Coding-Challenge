# ZidShip Courier Framework - Walkthrough

## 1. Overview
This project implements a unified courier integration framework for ZidShip using Django and Django REST Framework. It abstracts the complexity of multiple courier integrations (SMSA, Aramex, etc.) behind a single, consistent interface.

### Key Features
- **Unified Interface**: `CourierBase` abstract class defines the contract for all couriers.
- **Unified Data Models**: `Shipment` and `TrackingEvent` models normalize data across different providers.
- **Factory Pattern**: `CourierFactory` dynamically selects and instantiates courier strategies.
- **Mock Mode**: Built-in mock courier for testing without real credentials.
- **API Documentation**: Comprehensive Swagger/OpenAPI documentation via `drf-spectacular`.

## 2. Setup Instructions

### Prerequisites
- Python 3.8+
- PostgreSQL (optional, defaults to SQLite for development)

### Installation
1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd zidship_courier
    ```

2.  **Install dependencies**:
    ```bash
    pip install django djangorestframework drf-spectacular requests psycopg2-binary python-dotenv
    ```

3.  **Run Migrations**:
    ```bash
    python manage.py makemigrations core
    python manage.py migrate
    ```

4.  **Run Server**:
    ```bash
    python manage.py runserver
    ```

## 3. Verification

### running Automated Tests
Run the unit and integration tests:
```bash
python manage.py test core
```

### Running Manual Integration Test
Run the custom management command to simulate a full shipment lifecycle (Create -> Track -> Print Label -> Cancel):
```bash
python manage.py test_integration
```

### API Documentation (Swagger)
1.  Start the server: `python manage.py runserver`
2.  Navigate to: `http://localhost:8000/api/v1/docs/`

## 4. Architecture & Design Decisions

### Hexagonal Architecture
The core business logic (`ShipmentService`) is decoupled from the specific courier implementations (`SMSACourier`). The `CourierFactory` acts as the port, and the individual courier classes are adapters.

### JSONB for Flexibility
We used `JSONField` in the `Shipment` model to store courier-specific data. This allows us to keep the core schema clean while preserving all data returned by different providers.

### Trade-offs
-   **Synchronous API**: We implemented synchronous API endpoints for simplicity in this assessment. For a high-throughput production system, we would offload the courier API calls to background workers (Celery) to avoid blocking the request thread.
-   **Database**: We used SQLite for ease of setup in this demo, but the project is configured to easily switch to PostgreSQL for production.

## 5. Next Steps
-   Implement real Aramex integration using SOAP/REST.
-   Add Celery for asynchronous background processing.
-   Add comprehensive logging and monitoring (Sentry/Prometheus).

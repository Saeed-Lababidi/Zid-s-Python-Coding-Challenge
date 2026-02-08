# ZidShip Courier Framework

## Overview
A unified courier integration framework designed for ZidShip to abstract multiple courier integrations behind a single, consistent interface. Built with Django and Django REST Framework.

## System Architecture

The project follows a **Hexagonal Architecture (Ports and Adapters)** to decouple the core business logic from external concerns.

```mermaid
graph TD
    subgraph "Core Domain"
        Services[ShipmentService]
        Models[Shipment / TrackingEvent]
        Interfaces[CourierBase Interface]
    end

    subgraph "Adapters"
        API[REST API Views]
        SMSA[SMSA Courier Adapter]
        Mock[Mock Courier Adapter]
    end

    API --> Services
    Services --> Models
    Services --> Interfaces
    
    SMSA -.->|Implements| Interfaces
    Mock -.->|Implements| Interfaces
    
    Services --> SMSA
    Services --> Mock
```

## Challenge Requirements Mapping

The following table maps the requirements from the Python Coding Challenge PDF to the implementation in this project.

| Requirement | Implementation Component | File Location | Description |
| :--- | :--- | :--- | :--- |
| **Generic Interface** | `CourierBase` (Abstract Class) | `core/couriers/base.py` | Defines standard methods (`create_shipment`, `track`) that all couriers must implement. |
| **Specific Courier** | `SMSACourier` | `core/couriers/smsa.py` | Real SOAP integration with SMSA Express, constructing XML payloads for `addShipPDF`. |
| **Mock Courier** | `MockCourier` | `core/couriers/mock.py` | In-memory courier simulation for testing without external API calls. |
| **HTTP Retries** | `HTTPClient` | `core/http_client.py` | Robust HTTP wrapper with exponential backoff for handling network failures. |
| **Service Layer** | `ShipmentService` | `core/services.py` | Orchestrates validation, courier selection, api calls, and database persistence. |
| **REST API** | Django REST Framework | `core/views.py` | API endpoints to expose shipment functionality. |

## 🏗️ Architecture & Trade-off Analysis

The focus of this implementation was not just code, but architectural resilience and scalability. Here is a breakdown of the key technical choices and the trade-offs involved.

### 1. Database Choice: PostgreSQL + JSONB
**Decision**: We used PostgreSQL and heavily utilized `JSONField` (JSONB) for storing shipment details (Sender, Recipient, Package).
*   **Why**: 
    *   **Flexibility**: Courier integrations are messy. SMSA has different fields than Aramex or DHL. Creating normalized tables for every possible courier field results in a complex Entity-Attribute-Value (EAV) mess or sparse tables with hundreds of null columns.
    *   **Performance**: Postgres JSONB allows indexing specific keys inside the JSON (e.g., searching by `sender_phone` inside the JSON blob is fast).
*   **Trade-off**: 
    *   **Cons**: We lose some strict schema validation at the database level. 
    *   **Mitigation**: We enforce strict validaton at the application level using **Pydantic DTOs** and **DRF Serializers** before data ever reaches the DB.

### 2. Message Broker: In-Memory vs. Redis/Celery
**Decision**: Implemented a `SimpleMessageBroker` (`core/task_queue.py`) using Python threads for the assessment, but designed the system to swap this out for Celery/Redis in production.
*   **Why**: 
    *   **Simplicity**: Setting up a full Redis instance for a coding assessment adds unnecessary complexity to the setup process.
    *   **Demonstration**: The `SimpleMessageBroker` demonstrates the *pattern* of offloading non-critical tasks (like sending email notifications or webhooks) to a background worker without blocking the main API thread.
*   **Trade-off**: 
    *   **Cons**: If the web server restarts, the in-memory queue is lost. It doesn't scale across multiple servers.
    *   **Production Plan**: In a real ZidShip deployment, we would replace `core/task_queue.py` with **Celery** backed by **Redis** or **RabbitMQ** to ensure persistence and horizontal scaling.

### 3. Hexagonal Architecture (Ports & Adapters)
**Decision**: Core business logic (`ShipmentService`) is completely isolated from the "Outside World" (API Views and Courier Implementations).
*   **Why**: 
    *   **Testability**: We can test the Service layer with a `MockCourier` without ever making a network call.
    *   **Swap-ability**: We can switch from SMSA to Aramex, or from REST API to GraphQL, without changing a single line of the Core Service logic.

### 4. Synchronous vs. Asynchronous Courier Calls
**Decision**: The `create_shipment` API calls the courier API synchronously (blocking).
*   **Trade-off**:
    *   **Pros**: Immediate feedback to the user. They get the actual Waybill number instantly.
    *   **Cons**: If SMSA is down or slow, our API hangs.
    *   **Scaling Strategy**: For high throughput, we would move the courier call itself to the background queue, return a `request_id` to the user, and have them poll a status endpoint or receive a webhook (Async Implementation).

## Setup Instructions

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Migrations**:
    ```bash
    python manage.py makemigrations core
    python manage.py migrate
    ```

3.  **Run Server**:
    ```bash
    python manage.py runserver
    ```

## 🧪 Testing & Usage Guide

### 1. Automated Tests

**Run all Unit Tests (Core + SMSA):**
```bash
python manage.py test core
```

**Run only SMSA SOAP Integration Tests:**
```bash
python manage.py test core.tests_smsa
```

**Run Full Integration Scenario (Create -> Track -> Cancel):**
```bash
python manage.py test_integration
```

### 2. Manual Testing (Functionality Examples)

You can test the API using `curl` or Postman. Ensure the server is running: `python manage.py runserver`

#### A. List Available Couriers
```bash
curl -X GET http://localhost:8000/api/v1/couriers/
```

#### B. Create a Shipment
```bash
curl -X POST http://localhost:8000/api/v1/shipments/ \
  -H "Content-Type: application/json" \
  -d '{
    "reference_number": "ORDER-1001",
    "courier_provider": "MOCK", 
    "sender": {
      "name": "Zid Store",
      "address_line1": "Riyadh Business Gate",
      "city": "Riyadh",
      "country": "SA",
      "phone": "+966500000000"
    },
    "recipient": {
      "name": "Saeed Customer",
      "address_line1": "King Abdulaziz Road",
      "city": "Jeddah",
      "country": "SA",
      "phone": "+966511111111"
    },
    "package": {
      "weight": 2.5,
      "description": "Mobile Phone",
      "value": 3000
    }
  }'
```
*Response will contain a `waybill_number` (e.g., `MOCK...`). Use this for subsequent requests.*

#### C. Track a Shipment
```bash
curl -X GET http://localhost:8000/api/v1/shipments/<WAYBILL_NUMBER>/track/
```

#### D. Print Label
```bash
curl -X GET http://localhost:8000/api/v1/shipments/<WAYBILL_NUMBER>/label/
```

#### E. Cancel Shipment
```bash
curl -X DELETE http://localhost:8000/api/v1/shipments/<WAYBILL_NUMBER>/cancel/ \
  -H "Content-Type: application/json" \
  -d '{"reason": "Customer changed mind"}'
```

### 3. Testing SMSA Integration specifically
To test the real SMSA SOAP generation logic (without sending to the production server), we have created a dedicated test suite.

**File**: `core/tests_smsa.py`

**What it tests**:
1.  **XML Construction**: Verifies that the internal DTOs are correctly converted into the SOAP XML format expected by SMSA.
2.  **Response Parsing**: Verifies that the system can correctly parse a standard SMSA XML response.
3.  **Error Handling**: Ensures that SOAP faults or API errors are caught and converted to standard `errors` list.

**Run it:**
```bash
python manage.py test core.tests_smsa
```

## Documentation

- **API Docs**: Visit `/api/v1/docs/` after starting the server.
- **Architecture**: See `architecture.md` for detailed diagrams and interview guide.

# ZidShip Courier Framework Implementation Plan

## Goal Description
Design and implement a unified courier integration framework for ZidShip using **Python (Django)**. The goal is to abstract the complexity of 35+ courier integrations behind a single, consistent interface, allowing the system to scale without frequent refactoring.

## 1. Architectural Design

### 1.1 High-Level Architecture
The system will follow a **Hexagonal Architecture (Ports and Adapters)** principle:
- **Core Domain**: Shipment logic, Status normalization, unified data models.
- **Ports**: `CourierStrategy` interface (Abstract Base Class).
- **Adapters**: Specific implementations for SMSA, Aramex, etc.
- **Infrastructure**: Django ORM (PostgreSQL), Celery (Async Tasks), Redis (Caching/Locking).

### 1.2 Design Patterns
1.  **Strategy Pattern**: Use an abstract base class `CourierBase` to define the contract. Concrete classes (`SMSACourier`, `AramexCourier`) implement this contract.
2.  **Factory Pattern**: A `CourierFactory` or `Registry` to instantiate the correct courier class based on the provider string (e.g., "SMSA").
3.  **Adapter Pattern**: implicit in the design, adapting 3rd-party APIs to our internal unified interface.
4.  **Service Layer**: A `ShipmentService` to handle business logic, calling the Factory -> Strategy -> Database.

## 2. Database Schema (PostgreSQL)

We will use a relational database with `JSONField` for flexibility.

### `Shipment` Model
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Primary Key |
| `waybill_number` | String | Unique index, returned by courier |
| `tracking_number` | String | Sometimes different from waybill |
| `courier_provider` | String | Enum: 'SMSA', 'ARAMEX', etc. |
| `status` | Enum | Unified Status: `PENDING`, `CREATED`, `IN_TRANSIT`, `DELIVERED`, `CANCELLED`, `FAILED` |
| `sender_data` | JSONB | Normalized sender info |
| `recipient_data` | JSONB | Normalized recipient info |
| `package_data` | JSONB | Normalized package info (weight, dims) |
| `courier_specific_data` | JSONB | Stores raw response or extra fields specific to the courier |
| `label_url` | String | URL to the PDF label |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

### `TrackingEvent` Model
| Field | Type | Description |
| :--- | :--- | :--- |
| `shipment` | FK | Link to Shipment |
| `status` | Enum | Unified Status |
| `raw_status` | String | Original status string from courier |
| `description` | String | Human readable description |
| `timestamp` | DateTime | When the event happened |
| `location` | String | City/Country of event |

## 3. Unified Interface (Abstract Base Class)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class ShipmentRequest:
    reference_number: str
    sender: Dict[str, Any]
    recipient: Dict[str, Any]
    package: Dict[str, Any]

@dataclass
class ShipmentResponse:
    waybill_number: str
    tracking_number: str
    label_url: Optional[str]
    courier_data: Dict[str, Any]

class CourierBase(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def create_shipment(self, request: ShipmentRequest) -> ShipmentResponse:
        """Creates a shipment and returns waybill/label."""
        pass

    @abstractmethod
    def track_shipment(self, waybill_number: str) -> Dict[str, Any]:
        """Returns unified content status and history."""
        pass

    @abstractmethod
    def print_label(self, waybill_number: str) -> str:
        """Returns PDF URL or base64 string."""
        pass

    @abstractmethod
    def cancel_shipment(self, waybill_number: str) -> bool:
        """Cancels shipment if supported."""
        pass
    
    @abstractmethod
    def map_status(self, raw_status: str) -> str:
        """Maps courier specific status to Unified Enum."""
        pass
```

## 4. Proposed Changes & Implementation Steps

### Phase 1: Core Setup
#### [NEW] `core/models.py`
- Define `Shipment`, `TrackingEvent`.
- Define `UnifiedStatus` Enum.

#### [NEW] `core/couriers/base.py`
- Implement `CourierBase` ABC.
- Implement Data Classes (DTOs) for Requests/Responses to ensure strict typing.

### Phase 2: Implementations
#### [NEW] `core/couriers/smsa.py`
- Implement `SMSACourier`.
- Use `requests` or `zeep` (if SOAP) for API communication.
- Implement Retry logic using `urllib3` `Retry` or a decorator.

#### [NEW] `core/couriers/factory.py`
- `get_courier(provider_name)` returns an instance of the specific courier class.

### Phase 3: API & Service
#### [NEW] `core/services.py`
- `ShipmentService.create_shipment(...)`:
    1. Validate input.
    2. Select courier.
    3. Call `courier.create_shipment`.
    4. Save to DB.
    5. Async task: fetch initial tracking (if needed).

#### [NEW] `api/views.py`
- `POST /api/v1/shipments/`: Create shipment.
- `GET /api/v1/shipments/{waybill}/`: Get details.
- `GET /api/v1/shipments/{waybill}/track/`: Track real-time.

### Phase 4: Reliability & Bonus
- **Mock Mode**: Add `MockCourier` for testing without keys.
- **HTTP Retries**: Middleware or adapter configuration for robust networking.
- **Async Tasks**: Use Celery for `track_shipment` if the API is slow, or for periodic polling.

## 5. Trade-offs & Architecture Decisions
### 5.1 SQL vs NoSQL
- **Decision**: PostgreSQL with `JSONB`.
- **Reason**: We need structured relational data for the core system (Orders <-> Shipments), but Couriers have highly variable payloads. `JSONB` gives us the schema flexibility of NoSQL with the data integrity of SQL.

### 5.2 Synchronous vs Asynchronous
- **Decision**: Hybrid.
- **Reason**: `create_shipment` usually needs to be Sync to give immediate feedback (Waybill) to the user. `tracking` can be on-demand (Sync) or periodic (Async). We will implement Sync endpoints for the assessment but architectural provision for Async (Celery) is recommended for scale.

### 5.3 Library Choice
- **Decision**: Django REST Framework (DRF).
- **Reason**: Standard, robust, and provides excellent serialization tools essential for validating the complex JSON payloads for shipments.

## 6. Verification Plan

### Automated Tests
1. **Unit Tests**:
    - Test `CourierBase` generic logic.
    - Test `SMSACourier` with `unittest.mock` to mock network calls.
    - Test `StatusMapping` logic.
2. **Integration Tests**:
    - `POST /shipments` flow using `MockCourier`.
    - Verify DB records are created.

### Manual Verification
1. **Swagger UI**:
    - Use DRF-Spectacular generated Swagger to manually trigger `create_shipment`.
2. **One-Click Script**:
    - `python manage.py test_integration` (Custom management command to run a full flow).

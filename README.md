# Decentralized Supply Chain Tracker (MVP)

**Description**
A microservices-based supply chain tracking platform with Saga pattern coordination and optional blockchain integration. Tracks shipments, warehouses, and deliveries, providing a transparent workflow from shipment creation to final delivery.

**Features**

* Shipment management (create, update, track status)
* Warehouse inventory tracking
* Delivery and courier management
* Saga-based workflow coordination for shipment lifecycle
* Optional blockchain recording for immutable shipment status

**Tech Stack**

* **Backend:** Python 3.11+, FastAPI / Pydantic
* **Messaging / Workflow:** Kafka (event-driven Saga coordination)
* **Persistence:** PostgreSQL / SQLAlchemy
* **Blockchain:** Hyperledger / Ethereum (optional)

**Microservices**

1. **Shipment Service** – handles shipment creation and tracking
2. **Warehouse Service** – manages warehouses and inventory records
3. **Delivery Service** – manages deliveries and couriers
4. **Saga Coordinator** – tracks workflow and state transitions
5. **Blockchain Service** – optional immutable recording

**Architecture**

* Layered architecture: `domain`, `ports`, `services`, `adapters`
* Each microservice has its own DB and event publishing ports
* Saga ensures consistent state across services

**Getting Started (MVP)**

1. Install dependencies: `pip install -r requirements.txt`
2. Run services locally (e.g., FastAPI + Uvicorn)
3. Use Kafka for event-driven workflow coordination

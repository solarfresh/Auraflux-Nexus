# 🌐 Auraflux-Nexus: The Generative AI Knowledge & Workflow Orchestrator

**Auraflux-Nexus** serves as the robust, Django-based backend API for the Auraflux ecosystem. It is the central nervous system that transforms complex **Interactive Search Process (ISP)** principles into actionable knowledge via structured data management and intelligent workflow coordination.

The **Nexus** acts as the crucial **bridge** between the user's interactive frontend experience (Auraflux-Beacon) and the deep knowledge streams, ensuring data consistency and orchestrating the multi-step research workflow.

---

## 🌟 Core Responsibilities and Architecture

Auraflux-Nexus manages the entire research lifecycle, from the initial user input to the final structured output, focusing on reliability and scalability.

### 1. Generative AI Agent Orchestration

* **Intelligent Task Handling:** Manages and coordinates multiple intelligent agents responsible for generating, refining, and evaluating research components (e.g., suggesting better questions, extracting keywords, assessing feasibility).
* **Prompt Management:** Maintains the library of complex prompts required to execute the ISP methodology, ensuring consistent and high-quality AI outputs.

### 2. Data Integrity and Structured Output

* **Source of Truth:** Serves as the authoritative source for all structured research data, including the **Reflection Log**, **Final Question Status (DRAFT/LOCKED)**, **Topic Keywords**, and **Scope Elements**.
* **Workflow Gates:** Enforces the business logic and flow control rules (ISP principles). It verifies that all necessary data conditions (e.g., question locked, minimum keywords met) are satisfied before allowing phase transitions (e.g., from Initiation to Exploration).
* **API Services:** Provides RESTful API endpoints for persistent data storage, retrieval, and updates from the frontend.

### 3. Real-Time Communication

* **Asynchronous Processing:** Handles complex, long-running agent tasks and manages the resulting output stream.
* **WebSocket Integration:** Utilizes WebSockets to facilitate real-time, bi-directional communication with the frontend, enabling live updates of chat messages, progress status, and structured data changes.

---

## 🏗️ Technical Stack

Auraflux-Nexus is built on a robust, asynchronous, and scalable architecture designed to handle complex, concurrent Generative AI workflows while guaranteeing data integrity.

| Component | Technology / Concept | Role in Auraflux-Nexus |
| :--- | :--- | :--- |
| **Backend Core** | **Django / Django REST Framework (DRF)** | Provides the robust API framework and serves as the foundation for the central state model (SSOT). |
| **Asynchronous Task Queue** | **Celery** | Acts as the **Event Dispatcher** to isolate the high latency of LLM reasoning (TR Agent) using the **Fire-and-Forget** pattern, ensuring non-blocking Web API execution and high throughput. |
| **Language** | **Python** | Primary language used for agent logic and backend services. |
| **State Management** | **InitiationPhaseData Model** | Serves as the **Single Source of Truth (SSOT)** for all structured data, ensuring data atomicity and consistency across all agents. |
| **Communication** | **WebSocket** | Used for real-time, non-blocking delivery of asynchronous results to the frontend, utilizing **Dual-Channel Isolation** for stream data and atomic state updates. |
| **Resource Optimization** | **Singleton Pattern** | Implemented via `worker_process_init` to ensure thread-safe, one-time initialization of resource-intensive components (e.g., LLM connections) within Celery workers. |
| **Configuration** | **Django Models (AgentRoleConfig)** | Implements the **Configuration as Data** principle, allowing dynamic instantiation and modification of agent behavior without code redeployment. |

-----

## 🚀 Getting Started

This guide provides instructions for setting up and running the Auraflux-Nexus backend using Docker Compose. This configuration launches all required services: the API server, database, message broker, and two dedicated Celery worker queues.

### Prerequisites

  * **Docker:** Installation of Docker Engine and Docker Compose (or Docker Desktop).
  * **Git:** For cloning the repository.

### 1\. Configuration Setup

The project uses environment files (`docker-vars.env`, `docker-vars.override.env`) to manage sensitive settings for various services.

1.  **Duplicate Environment Files:** Ensure you have your local configuration files ready.

    ```bash
    cp docker-vars.env.example docker-vars.env
    cp docker-vars.override.env.example docker-vars.override.env
    ```

2.  **Edit `docker-vars.env`:** Update the following mandatory variables in your **`.env`** file (especially for LLM API keys and Database credentials):

| Variable | Description | Example |
| :--- | :--- | :--- |
| `POSTGRES_USER` | Database superuser for Postgres. | `nexus_user` |
| `POSTGRES_PASSWORD` | Password for the database user. | `secure_db_pass` |
| `DJANGO_SECRET_KEY` | Django secret key (crucial for security). | `a_long_random_string` |
| `OPENAI_API_KEY` | Your key for accessing the Generative AI services. | `sk-xxxx` |

### 2\. Building and Launching Services

Use Docker Compose to build the custom application image (`auraflux-nexus:latest`) and launch all five defined services.

1.  **Create External Network:** As per your `docker-compose.yml`, the network is defined as `external: true`. You must create it first.

    ```bash
    docker network create auraflux_network
    ```

2.  **Build and Start All Services:** This command builds the `nexus` and starts all services: `postgres`, `redis`, `nexus` (Web API), `worker_default`, and `worker_stream`.

    ```bash
    docker-compose up --build -d
    ```

### 3\. Database Setup and Initial Administration (Crucial Step)

The database schema must be initialized, and the necessary default configurations and administrator accounts must be created.

1.  **Run Migrations:** Execute Django migrations to set up the database schema.

    ```bash
    docker-compose exec nexus python manage.py migrate
    ```

2.  **Create Initial Admin User and Agent Roles:** Execute the custom management command to create the first administrator account and set up the default `AgentRoleConfig` instances.

    ```bash
    docker-compose exec nexus python manage.py create_initial_admin
    ```

### 4\. Verification

  * **Web API (nexus):** The Django server should now be running and accessible at:
    `http://localhost:8000/`

  * **Celery Workers (`worker_default`, `worker_stream`):** Verify the workers are running and connected to the Redis message broker, confirming the two task queues (`celery,default` and `stream`) are active.

    ```bash
    docker-compose logs worker_default
    docker-compose logs worker_stream
    ```

The Auraflux-Nexus backend is now fully operational, with dedicated Celery workers ready to handle the Agent-centric asynchronous tasks.

---

## ⚖️ License

[Apache 2.0](LICENSE)
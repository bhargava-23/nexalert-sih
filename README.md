# NexAlert

**An open, ongoing project for early warning of environmental hazards.**

NexAlert watches the environment with small, low-cost sensor nodes. It spots danger early, such as a fire, a landslide or unsafe air. Then it helps people respond: officials see what is happening on a dashboard, and citizens get clear safety guidance on their phones.

It is built to keep working when things go wrong. Nodes keep their own data when the network drops. Citizens can reach a local Wi-Fi network even when the internet is down. And a **human always approves** an alert before it goes out.

> **Project status: active development.** Some parts are done and tested. Some parts are written but not yet tested end to end. Some parts are still ideas. The [status table](#current-status) tells you which is which. We try hard not to say a feature "works" until it has been checked.

---

## Table of contents

1. [What NexAlert does](#what-nexalert-does)
2. [Big picture](#big-picture)
3. [How data travels, step by step](#how-data-travels-step-by-step)
4. [The field node (hardware and firmware)](#the-field-node-hardware-and-firmware)
5. [Edge intelligence: how a node thinks](#edge-intelligence-how-a-node-thinks)
6. [The backend](#the-backend)
7. [Hazards, incidents and alerts](#hazards-incidents-and-alerts)
8. [Fire spread simulation](#fire-spread-simulation)
9. [Working without internet](#working-without-internet)
10. [The web apps](#the-web-apps)
11. [The telemetry contract](#the-telemetry-contract)
12. [Database](#database)
13. [API overview](#api-overview)
14. [Repository layout](#repository-layout)
15. [Getting started](#getting-started)
16. [Tests and checks](#tests-and-checks)
17. [Current status](#current-status)
18. [Roadmap](#roadmap)
19. [Safety and security notes](#safety-and-security-notes)
20. [Docs and design rules](#docs-and-design-rules)
21. [Contributing](#contributing)

---

## What NexAlert does

In plain words:

- **Sense.** Field nodes read temperature, humidity, pressure, gas and ground vibration.
- **Think at the edge.** Each node does a first round of reasoning on the device itself. It asks: "Are my sensors healthy? Is this reading normal for this place?"
- **Send safely.** Nodes send readings over MQTT. If the network is down, they store readings and send them later.
- **Check everything.** The backend checks each reading against one shared rulebook (the telemetry contract) before it trusts it.
- **Combine many nodes.** Readings from several nodes are fused into one regional picture. Related readings become one **incident**.
- **Model the danger.** For fires, the system can simulate how the fire may spread and which areas may be hit first.
- **Tell people.** Officials see nodes, hazards, incidents and SOS requests. Citizens see nearby hazards and safety actions. Alerts are sent as browser push notifications **after a person approves them**.

### Hazards covered

| Hazard | Where it stands |
|---|---|
| Fire | Most complete path: sensing, fusion, incidents, simulation, alerts |
| Landslide (ground vibration) | Vibration analyzer is wired into saving telemetry |
| Flood, pollution, extreme heat, other | The hazard model has room for them. Depth of support varies |

---

## Big picture

```mermaid
flowchart TD
    subgraph FIELD["Field (outdoors)"]
        N1["Field node 1<br/>ESP32-S3 + sensors"]
        N2["Field node 2<br/>ESP32-S3 + sensors"]
        N3["Field node N<br/>ESP32-S3 + sensors"]
    end

    subgraph LOCAL["Local hub (for example a Raspberry Pi)"]
        MQTT["MQTT broker<br/>(Mosquitto)"]
        AP["Wi-Fi access point<br/>for citizens"]
    end

    subgraph BACKEND["Backend (Python, FastAPI)"]
        ING["Ingestion<br/>validate + save"]
        INT["Intelligence<br/>fusion + incidents"]
        SIM["Simulation<br/>fire spread + risk map"]
        ALR["Alerts<br/>approve + push"]
        API["REST API"]
    end

    DB[("PostgreSQL + PostGIS")]

    subgraph WEB["Web apps"]
        AUTH["Authority dashboard<br/>for officials"]
        CIT["Citizen app (PWA)<br/>for the public"]
    end

    N1 -->|"telemetry"| MQTT
    N2 -->|"telemetry"| MQTT
    N3 -->|"telemetry"| MQTT
    MQTT --> ING
    ING --> DB
    ING --> INT
    INT --> DB
    INT -->|"fire incident"| SIM
    SIM --> DB
    INT -->|"alert recommendation"| ALR
    ALR --> DB
    DB --> API
    API --> AUTH
    API --> CIT
    AUTH -->|"human approves alert"| ALR
    ALR -->|"web push"| CIT
    AP -.->|"citizens join"| CIT
```

**One idea runs through the whole design:** each layer can do its job on its own. A node still thinks when the hub is gone. The hub still serves citizens when the internet is gone. The system recommends, and a human decides.

---

## How data travels, step by step

This is the full journey of one reading, from a sensor to a phone.

```mermaid
flowchart TD
    A["1. Node reads sensors"] --> B["2. Node runs edge intelligence<br/>health, quality, anomaly, state"]
    B --> C["3. Node builds a telemetry envelope (JSON)"]
    C --> D{"Is the network up?"}
    D -->|"Yes"| E["4. Publish to MQTT<br/>Nexalert/telemetry/&lt;node&gt;"]
    D -->|"No"| F["Save in local buffer"]
    F -->|"Network returns"| E
    E --> G["5. Backend receives the message"]
    G --> H{"6. Valid against<br/>the shared schema?"}
    H -->|"No"| X["Reject and log"]
    H -->|"Yes"| I["7. Save to database"]
    I --> J["8. Run vibration analysis<br/>(landslide check)"]
    I --> K["9. Regional fusion<br/>combine nearby nodes"]
    K --> L{"10. Do the nodes agree<br/>enough to call it an incident?"}
    L -->|"No"| M["Keep watching"]
    L -->|"Yes"| N["11. Create or update incident"]
    N --> O{"Is it a fire?"}
    O -->|"Yes"| P["12. Start fire simulation"]
    O -->|"No"| Q["13. Create alert recommendation"]
    P --> Q
    Q --> R["14. Human reviews and approves"]
    R --> S["15. Web push to citizens"]
    S --> T["16. Citizen sees guidance<br/>and can send SOS"]
```

Some steps are code-complete but not yet proven on real hardware. See [Current status](#current-status).

---

## The field node (hardware and firmware)

The node is the part you put outside. The firmware lives in `firmware/` and is an **ESP-IDF 5.1.x** project for the **ESP32-S3**.

### Sensors in the code

| Sensor | What it gives | Driver |
|---|---|---|
| BME680 | Humidity, pressure, gas resistance | `firmware/components/sensors/bme680.c` |
| KY-028 | Temperature | `ky028.c` |
| MPU-6050 family accelerometer | Ground vibration | `mpu6050.c` |
| MQ-2 | Smoke and gas (raw ADC value, **not** ppm) | `mq2.c` |
| DHT22 | Older temperature and humidity driver | `dht22.c` |

### Firmware parts

| Folder in `firmware/components/` | Job | State |
|---|---|---|
| `sensors/` | Read the sensors | Written |
| `intelligence/` | Edge reasoning in C (see next section) | Written, with unit tests |
| `telemetry/` | Build the JSON envelope | Written |
| `network/` | Wi-Fi, MQTT, time sync (SNTP) | Written |
| `resilience/` | Store-and-forward buffer and node heartbeat | Written, buffer has a test |
| `config/` | Node settings and stored calibration | Written |
| `local_ap/` | Emergency Wi-Fi access point | Header only (planned) |
| `security/` | Message signing (HMAC) | Header only (planned) |
| `storage/`, `system/`, `diagnostics/` | Extra helpers | Headers only (planned) |

### What the node does in a loop

```mermaid
flowchart TD
    START(["Boot"]) --> CAL["Load calibration<br/>from flash"]
    CAL --> WIFI["Connect Wi-Fi"]
    WIFI --> TIME["Sync time (SNTP)"]
    TIME --> MQ["Connect MQTT"]
    MQ --> LOOP

    subgraph LOOP["Main loop"]
        direction TB
        S["Read sensors"] --> V{"Reading valid?"}
        V -->|"No"| MISS["Mark as MISSING<br/>(never turn it into 0)"]
        V -->|"Yes"| SM["Smooth vibration<br/>with a moving average"]
        MISS --> INTEL
        SM --> INTEL["Run intelligence chain"]
        INTEL --> BUILD["Build telemetry JSON"]
        BUILD --> PUB["Publish, or buffer if offline"]
        PUB --> HB{"Heartbeat due?"}
        HB -->|"Yes"| HBS["Send heartbeat<br/>and replay buffered data"]
        HB -->|"No"| S
        HBS --> S
    end
```

**Store and forward.** If MQTT is unreachable, the node puts messages in a buffer with a priority. When the node reconnects, it replays up to 50 buffered messages per heartbeat cycle. This avoids flooding the network on recovery.

**Build and flash** (needs ESP-IDF 5.1.x and a real board):

```bash
. "$IDF_PATH/export.sh"
cd firmware
idf.py set-target esp32s3
idf.py build
idf.py flash monitor
```

More detail: `firmware/BUILD_INSTRUCTIONS.md`. Note that `firmware/README.md` is older than the code and still says "structure only". The source files are the better guide for now.

---

## Edge intelligence: how a node thinks

Every node runs a small chain of calculations. Each step answers one clear question. Keeping them apart is on purpose: **health, quality, reliability, confidence, severity and risk are different things** and must not be mixed up.

```mermaid
flowchart LR
    H["Health<br/>Is the sensor<br/>working?"] --> R
    Q["Quality<br/>Is this reading<br/>clean?"] --> R
    K["Calibration<br/>Is the sensor<br/>tuned?"] --> R
    R["Reliability<br/>Can I trust<br/>this sensor?"]
    B["Baseline<br/>What is normal<br/>here?"] --> Z["Z-score<br/>How far from<br/>normal?"]
    Z --> A["Anomaly<br/>How odd is<br/>it?"]
    A --> E["Evidence<br/>How much<br/>proof for a hazard?"]
    R --> C["Confidence<br/>How sure am I?"]
    E --> C
    E --> SV["Severity<br/>How bad<br/>would it be?"]
    C --> RK["Risk"]
    SV --> RK
    RK --> ST["Hazard state"]
```

### Hazard states

A node (and later the region) moves through these states for each hazard type.

```mermaid
stateDiagram-v2
    [*] --> NORMAL
    NORMAL --> WATCH: "something unusual"
    WATCH --> SUSPECTED: "evidence grows"
    SUSPECTED --> CONFIRMED: "strong evidence"
    CONFIRMED --> CRITICAL: "severe and spreading"
    WATCH --> NORMAL: "back to normal"
    SUSPECTED --> WATCH: "evidence fades"
    CONFIRMED --> RESOLVED: "danger over"
    CRITICAL --> RESOLVED: "danger over"
    RESOLVED --> NORMAL
```

### Two copies of the same math (on purpose)

The same calculations exist twice:

- **C** in `firmware/components/intelligence/` (runs on the node)
- **Python** in `reference/python/nexalert_reference/` (the readable reference)

Shared test cases in `tests/golden-vectors/` and in the test folders check that both give the same answer. If you change a formula, change both and run both test suites.

---

## The backend

The backend is a FastAPI app in `services/backend/`. It is one app split into clear modules. It is **not** a set of separate microservices.

| Module | Folder | What it does |
|---|---|---|
| Ingestion | `modules/ingestion/` | MQTT consumer, schema validator, node registry, database saver |
| Intelligence | `modules/intelligence/` | Regional fusion, incident correlation, the coordinator that ties them together |
| Hazards | `modules/hazards/` | Vibration analyzer, fire spread model, risk surface |
| Geospatial | `modules/geospatial/` | Coordinate transforms, terrain, geometry, propagation |
| Simulation | `modules/simulation/` | Fire simulation runner, exposure calculator, trigger coordinator |
| Alerts | `modules/alerts/` | Alert lifecycle and Web Push delivery |
| SOS | `modules/sos/` and `routes_sos.py` | Citizen emergency requests |
| API | `modules/api/` | All HTTP routes |

### Inside the backend: what happens to one message

```mermaid
flowchart TD
    M["MQTT message<br/>Nexalert/telemetry/&lt;node&gt;"] --> P["Parse JSON"]
    P --> V["Validate against<br/>schemas/telemetry-envelope.schema.json"]
    V --> NID{"Node ID looks like<br/>NODE-123?"}
    NID -->|"No"| REJ["Reject"]
    NID -->|"Yes"| NR["Check or register node"]
    NR --> NORM["Normalize payload"]
    NORM --> SAVE[("Save to<br/>telemetry_records")]
    SAVE --> VIB["Vibration analysis"]
    VIB -->|"state is not NORMAL"| HA[("Save hazard assessment")]
    SAVE --> CO["Intelligence coordinator<br/>(runs without blocking MQTT)"]
    CO --> OBS["Collect recent observations<br/>from nearby nodes"]
    OBS --> FUSE["Regional fusion"]
    FUSE --> COR["Incident correlation"]
    COR --> INC[("Create or update incident")]
    INC --> FIRE{"Hazard is FIRE?"}
    FIRE -->|"Yes"| TRIG["Trigger fire simulation"]
```

Important rules the code follows:

- **Missing is not zero.** A missing reading stays missing all the way through.
- **Two clocks.** The time a reading was *measured* and the time the backend *received* it are separate fields.
- **Local state is never erased.** If the region disagrees with a node, the node's own state is kept.
- **Non-blocking.** Fusion and simulation run without slowing down message intake. If they fail, intake keeps going.
- **Idempotent.** The same observation is linked to an incident only once.

---

## Hazards, incidents and alerts

### From readings to an incident

Many nodes may see the same event. The backend groups them.

```mermaid
flowchart TD
    O["New observations from nodes"] --> F["Weigh each one:<br/>how fresh? how reliable?"]
    F --> D["Freshness fades over time<br/>(half-life about 5 min,<br/>too old after 30 min)"]
    D --> AG["Compute agreement<br/>between nodes"]
    AG --> RG["Regional confidence,<br/>severity and risk"]
    RG --> NEAR{"Is there an open incident<br/>of this hazard within about 50 m<br/>and 30 s?"}
    NEAR -->|"Yes"| UPD["Update that incident"]
    NEAR -->|"No"| NEW["Create a new incident"]
```

### Incident life

```mermaid
stateDiagram-v2
    [*] --> NEW
    NEW --> ACTIVE: "more evidence"
    ACTIVE --> ESCALATED: "gets worse"
    ESCALATED --> ACTIVE: "calms down"
    ACTIVE --> RESOLVED: "danger over"
    ESCALATED --> RESOLVED: "danger over"
    RESOLVED --> [*]
```

### Alert life: a human is always in the loop

```mermaid
flowchart LR
    R["RECOMMENDATION<br/>(system suggests)"] --> HUM{"Authorized person<br/>reviews"}
    HUM -->|"Approves"| I["ISSUED"]
    HUM -->|"Rejects"| X(["No alert sent"])
    I --> DL["DELIVERING<br/>(push sent)"]
    DL --> D["DELIVERED"]
    D --> SD["STAND_DOWN<br/>(all clear)"]
```

Alert severities are `ADVISORY`, `WARNING` and `CRITICAL`. Each alert has a title, a message and plain action guidance for citizens. Delivery to each device is tracked (pending, sent, failed, unreachable).

---

## Fire spread simulation

When a fire incident appears, the backend can model how it may spread. This is a simplified model, built to be improved over time.

```mermaid
flowchart TD
    TR["Fire incident created"] --> CO["Simulation coordinator"]
    CO --> IN["Gather inputs:<br/>fire location, fuel, moisture,<br/>wind, slope"]
    IN --> ROS["Compute rate of spread<br/>in each direction"]
    ROS --> GRID["Grow fire across a grid<br/>over time"]
    GRID --> AT["Arrival times<br/>when does fire reach each cell?"]
    GRID --> GEO["Fire shapes<br/>(geometry for the map)"]
    GRID --> RS["Risk surface"]
    GEO --> EXP["Exposure calculation<br/>who and what is in the way?"]
    AT --> DBS[("Save simulation,<br/>geometries, risk surface, exposure")]
    RS --> DBS
    EXP --> DBS
```

How speed is worked out:

- Each **fuel type** has a base speed: grass (fast), brush (medium), forest (slower). Non-burnable ground and water do not burn.
- **Moisture** slows the fire.
- **Wind** pushes the fire in the direction the wind blows toward. The code carefully converts "wind from" into "wind toward".
- **Slope** helps fire climb uphill.
- Wind and slope together make the spread uneven, so the fire grows into an oval and not a circle.

A simulation can also be started by hand with `POST /api/simulations/start`.

---

## Working without internet

Emergencies often break the network. NexAlert is designed so citizens can still get help from a local network.

```mermaid
flowchart TD
    subgraph HUB["Local hub (Raspberry Pi)"]
        BR["MQTT broker"]
        BE["Backend on :8000"]
        UI["Citizen app"]
        HP["Wi-Fi hotspot<br/>(hostapd + dnsmasq)"]
    end
    NODES["Field nodes"] -->|"local MQTT"| BR
    BR --> BE
    BE --> UI
    HP --> PH["Citizen phones<br/>join the Wi-Fi"]
    PH -->|"open page"| UI
    PH -.->|"live updates<br/>(WebSocket)"| BE
    NET(("Internet")) -. "may be down" .- HUB
```

- Everything the citizen app needs can run on the hub itself.
- The backend answers the "captive portal" checks that phones send when they join a Wi-Fi network (`/generate_204`, `/hotspot-detect.html`, `/ncsi.txt`), so the phone opens the app on connect.
- Setup steps: [`docs/OFFLINE_LOCAL_NETWORK_SETUP.md`](docs/OFFLINE_LOCAL_NETWORK_SETUP.md).
- A live WebSocket feed (`/ws/emergency-updates`) is written. It is **not mounted in `main.py` yet**, so it is not reachable today. See the [roadmap](#roadmap).

---

## The web apps

There are two families of apps. The Next.js apps are the original ones. The Vite apps are newer and have more screens.

| App | Folder | Built with | For | Screens |
|---|---|---|---|---|
| Authority dashboard | `apps/authority-dashboard/` | Next.js 14, React 18, Tailwind | Officials | Home, monitoring, nodes and node detail, hazards, map, SOS |
| Citizen web | `apps/citizen-web/` | Next.js 14, React 18, Tailwind | Public | Conditions, nearby hazards, safety status, emergency actions. Has a service worker and PWA manifest |
| Authority dashboard (v2) | `apps/v0-authority-dashboard/` | Vite, React, Tailwind, Radix UI | Officials | Overview, incidents, fire spread, multi-hazard, nodes, telemetry, citizen SOS, system |
| Citizen UI (v2) | `apps/v0-citizen-ui/` | Vite, React, Tailwind, Radix UI | Public | Home, map, safe places, alerts, SOS, event details, notification settings |

Some v2 pages show an "unavailable" screen on purpose, because the backend does not support them yet: affected area, alerts admin, history, response and audit.

### How a citizen gets a push alert

```mermaid
sequenceDiagram
    participant C as Citizen browser
    participant SW as Service worker
    participant B as Backend
    participant O as Official (dashboard)

    C->>B: GET /api/v1/alerts/vapid-public-key
    C->>SW: Register service worker
    C->>SW: Subscribe to push with the key
    C->>B: POST /api/v1/alerts/subscribe
    C->>B: POST /api/v1/alerts/update-location
    Note over B: Incident appears,<br/>alert is RECOMMENDED
    O->>B: Approve alert
    B->>SW: Web Push message
    SW->>C: Show notification
    C->>B: GET /api/v1/alerts/citizen
```

Browsers only allow service workers on HTTPS (or `localhost`).

---

## The telemetry contract

All parts of NexAlert agree on one message format. It is defined once, in `schemas/telemetry-envelope.schema.json`.

Every message has these top-level fields:

| Field | Meaning |
|---|---|
| `schema_version` | Version of the format, so it can grow safely |
| `telemetry_id` | Unique ID (ULID recommended) |
| `node_id` | Registered node name, like `NODE-001` |
| `sequence` | Counter per node, for ordering and spotting replays |
| `measurement_timestamp` | When the node measured it (UTC) |
| `received_timestamp` | When the backend got it (set by the server) |
| `location` | Where the node is |
| `measurements` | Sensor values. All optional. Missing means missing, **not zero** |
| `diagnostics` | Health signals used to judge sensor health |
| `power` | Battery and power state |
| `source` | `HARDWARE` or `SIMULATION`, so real and test data never mix |
| `auth` | Planned message signing (HMAC) |

Where the contract lives in code:

- `schemas/telemetry-envelope.schema.json` (the source of truth)
- `packages/nexalert-events/` (Python)
- `packages/nexalert-types/` (TypeScript)
- `tests/golden-vectors/` and each package's tests (keep them in sync)

---

## Database

PostgreSQL 15 with PostGIS. Tables are created through migrations in `db/` and `services/backend/db/`.

```mermaid
erDiagram
    NODES ||--o{ TELEMETRY_RECORDS : sends
    TELEMETRY_RECORDS ||--o{ SENSOR_ASSESSMENTS : has
    TELEMETRY_RECORDS ||--o{ HAZARD_ASSESSMENTS : has
    NODES ||--o| NODE_STATUS : tracked_by
    INCIDENTS ||--o{ INCIDENT_OBSERVATIONS : groups
    INCIDENTS ||--o{ REGIONAL_HAZARD_ASSESSMENTS : scored_by
    INCIDENTS ||--o{ INCIDENT_HAZARD_ASSESSMENTS : scored_by
    INCIDENTS ||--o{ FIRE_SIMULATIONS : triggers
    FIRE_SIMULATIONS ||--o{ FIRE_GEOMETRIES : produces
    FIRE_SIMULATIONS ||--o{ RISK_SURFACES : produces
    FIRE_SIMULATIONS ||--o{ EXPOSURES : produces
    INCIDENTS ||--o{ ALERTS : leads_to
    ALERTS ||--o{ ALERT_DELIVERIES : delivered_by
    PUSH_SUBSCRIPTIONS ||--o{ ALERT_DELIVERIES : receives
    SOS_REQUESTS
```

Alert delivery tables: `alerts`, `push_subscriptions`, `alert_deliveries`. Citizen emergency requests go in `sos_requests`.

---

## API overview

Run the backend and open **`http://localhost:8000/docs`** for the live, interactive docs. Routes below are the main ones found in the code.

| Area | Routes |
|---|---|
| Health | `GET /health` |
| Nodes | `GET /api/v1/nodes`, `GET /api/v1/nodes/{node_id}` |
| Telemetry | `GET /api/v1/telemetry/latest`, `GET /api/v1/telemetry/{node_id}` |
| Assessments | `GET /api/v1/sensor-assessments`, `GET /api/v1/hazards`, per-node versions under `/api/v1/nodes/{node_id}/...` |
| Incidents | `GET /api/incidents`, `GET /api/incidents/{id}`, `.../observations`, `.../geometries` |
| Regional | `GET /api/regional-hazards`, `GET /api/node-status` |
| Fire simulation | `POST /api/simulations/start`, `GET /api/simulations`, `GET /api/simulations/{id}`, `.../geometries` |
| Alerts and push | `GET /api/v1/alerts/vapid-public-key`, `POST .../subscribe`, `POST .../unsubscribe`, `POST .../update-location`, `GET .../citizen`, `POST .../test-push` |
| SOS | `POST /api/v1/sos`, `GET /api/v1/sos`, `GET /api/v1/sos/{id}`, `PATCH /api/v1/sos/{id}` |
| Demo and test | `POST /demo/trigger-fire`, `POST /demo/reset`, `GET /demo/status`, `POST /api/test/create-fire-incident`, `POST /api/test/resolve-incident/{id}`, `GET /api/test/list-test-incidents` |

Notes:

- Two route prefixes exist today (`/api/v1/...` and `/api/...`). This is history, and tidying it is on the roadmap.
- An empty, unmigrated database will return empty lists. That is normal.
- Demo routes return scripted data. They are for presentations and screenshots, not real monitoring.

---

## Repository layout

```text
.
├── apps/
│   ├── authority-dashboard/      # Officials' dashboard (Next.js)
│   ├── citizen-web/              # Citizen app + service worker (Next.js)
│   ├── v0-authority-dashboard/   # Newer dashboard (Vite)
│   └── v0-citizen-ui/            # Newer citizen app (Vite)
├── db/                           # Alembic migrations
├── demo/                         # start.sh / start.ps1 helper scripts
├── docs/
│   ├── implementation/           # Design decisions, phase and track reports
│   ├── specifications/           # Original specification documents
│   ├── specification_text/       # Same specs as text
│   ├── architecture/, runbooks/  # Placeholders to fill in
│   └── OFFLINE_LOCAL_NETWORK_SETUP.md
├── firmware/                     # ESP32-S3 node firmware (ESP-IDF)
│   ├── main/                     # Entry point and calibration store
│   └── components/               # sensors, intelligence, network, ...
├── infra/docker/                 # docker-compose for PostGIS
├── lib/                          # Generated API client, zod types, drizzle setup
├── packages/                     # Shared code
│   ├── nexalert-events/          # Telemetry types (Python)
│   ├── nexalert-types/           # Telemetry types (TypeScript)
│   ├── nexalert-config/
│   └── nexalert-ui-components/
├── reference/python/             # Readable reference of the intelligence math
├── schemas/                      # The telemetry contract (JSON Schema)
├── scripts/                      # Pi setup, MQTT subscriber, lint helpers
├── services/backend/             # FastAPI backend
│   ├── modules/                  # ingestion, intelligence, hazards, ...
│   ├── db/                       # Models and migration helpers
│   └── tests/
├── tests/golden-vectors/         # Shared expected outputs for the math
└── *.md                          # Implementation and verification reports
```

---

## Getting started

### What you need

- Python 3.11 or newer
- Node.js 20 or newer, and pnpm
- PostgreSQL 15 with PostGIS 3.3 (or use Docker below)
- An MQTT broker such as Mosquitto, if you want live node data
- ESP-IDF 5.1.x and a real ESP32-S3 board, **only** for firmware work

### 1. Start the database

Easiest way, with Docker:

```bash
docker compose -f infra/docker/docker-compose.yml up -d
```

This starts PostGIS with a database called `nexalert_dev`. Then point the backend at it:

```bash
export DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@localhost:5432/nexalert_dev"
```

Apply migrations from `db/` and `services/backend/db/`. Read the migration notes first. Never run them against data you care about without a backup.

### 2. Start the backend

```bash
cd services/backend
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env               # then edit values
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Check it:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`

Main settings (set in `.env`): `DATABASE_URL`, `MQTT_BROKER_HOST`, `MQTT_BROKER_PORT`, `MQTT_TOPIC` (default `Nexalert/telemetry/+`), `MQTT_USERNAME`, `MQTT_PASSWORD`, `TELEMETRY_SCHEMA_PATH`.

### 3. Start the web apps

From the repository root:

```bash
pnpm install
```

**Next.js apps** (original):

```bash
# apps/authority-dashboard/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# apps/citizen-web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

```bash
pnpm --filter authority-dashboard dev                 # http://localhost:3000
pnpm --filter citizen-web dev -- --port 3001          # http://localhost:3001
```

**Vite apps** (newer). Run these from inside each app folder. They need `PORT` and `BASE_PATH`, and you should set the backend address:

```bash
cd apps/v0-authority-dashboard
PORT=5173 BASE_PATH=/ VITE_API_BASE_URL=http://localhost:8000/api/v1 pnpm dev

cd apps/v0-citizen-ui
PORT=5174 BASE_PATH=/ VITE_API_BASE_URL=http://localhost:8000 pnpm dev
```

If you skip `VITE_API_BASE_URL`, the Vite apps fall back to a hard-coded demo address. Always set it yourself.

### 4. Try it without hardware

You do not need a node to see the system work.

1. Start the database, backend and one web app.
2. Call `POST http://localhost:8000/demo/trigger-fire` for scripted demo data.
3. Or use `POST /api/test/create-fire-incident` to make a test incident in the database.
4. Or publish your own message to MQTT using one of the sample files such as `services/backend/test_telemetry.json`. Set `"source": "SIMULATION"` so it is clearly marked as a test.
5. Several ready-made scenarios live in `services/backend/scenario_*.json`: a single odd node, several agreeing nodes, nodes that disagree, stale data, an unhealthy node, duplicate messages and incident resolution.

You can also use `demo/start.sh` (Linux and macOS) or `demo/start.ps1` (Windows) to start many pieces at once. Read them first. The Windows script stops any process using ports 8000, 3000 and 3001.

### 5. Set up a Raspberry Pi hub

`scripts/setup_pi.sh` and `scripts/pi_mqtt_subscriber.py` help set up a hub. For the local Wi-Fi network, follow [`docs/OFFLINE_LOCAL_NETWORK_SETUP.md`](docs/OFFLINE_LOCAL_NETWORK_SETUP.md).

---

## Tests and checks

| What | Where | How |
|---|---|---|
| Backend tests | `services/backend/tests/` | `cd services/backend && pytest` |
| Telemetry contract (Python) | `packages/nexalert-events/tests/` | `pytest packages/nexalert-events` |
| Telemetry contract (TypeScript) | `packages/nexalert-types/` | `pnpm --filter nexalert-types test` |
| Intelligence math (Python) | `reference/python/tests/` | `pytest reference/python` |
| Intelligence math (C) | `firmware/components/intelligence/test/` | Built with the firmware |
| Frontend lint and build | `apps/*` | `pnpm --filter <app> lint` and `build` |
| Formatting | whole repo | `black`, `ruff`, `prettier`, `clang-format` |

A GitHub Actions workflow in `.github/workflows/ci.yml` runs linting, tests and builds. Some CI steps are forgiving, and the firmware build is skipped when ESP-IDF is missing. **A green CI run does not prove the whole system works.** Real-world testing still matters.

---

## Current status

Honest, per feature. "Written" means the code exists. "Verified" means someone ran it and saw it work.

| Area | Status |
|---|---|
| Telemetry contract and shared types | Written and tested |
| Edge intelligence (C and Python) | Written, with shared test cases |
| Sensor drivers and node main loop | Written. Needs more field testing |
| Store-and-forward buffer and heartbeat | Written, with a unit test |
| MQTT ingestion, validation, saving | Written and tested in the backend suite |
| Regional fusion and incident correlation | Written and tested |
| Vibration (landslide) analysis | Written and called when telemetry is saved. Needs real accelerometer data to prove it |
| Fire spread model, risk surface, exposure | Written |
| Fire simulation auto-start on a fire incident | Hook is in the code. Needs end-to-end proof |
| Alert lifecycle and Web Push (backend) | Written. VAPID key endpoint and database tables checked |
| Web Push in a real browser | **Not verified** (needs HTTPS or localhost browser test) |
| SOS requests | Written |
| Authority and citizen apps | Written. Some v2 pages are placeholders |
| MQ-2 gas value in fire evidence | **Not done.** The value is sent and saved, but not used in fire scoring yet |
| WebSocket live feed | Written but **not mounted** in `main.py` |
| Local emergency Wi-Fi on the node | **Planned** (header only) |
| Message signing (HMAC) | **Planned** (field exists in the contract) |
| Field accuracy and sensor calibration | **Not measured yet** |

Dated notes with evidence: `VERIFICATION_RESULTS.md`, `IMPLEMENTATION_REPORT.md`, `PHASE_4_COMPLETE.md`, `POWER_RECOVERY_REPORT.md`, and the files in `docs/implementation/`.

---

## Roadmap

Rough order of work. This list will change as we learn.

**Next up**
- Mount the WebSocket router and connect both apps to live updates.
- Use the MQ-2 gas value in fire evidence.
- Test Web Push in a real browser with HTTPS, including click-through and delivery tracking.
- Prove the full path with real hardware: node to MQTT to backend to incident to alert to phone.

**Soon**
- Build the node's local emergency Wi-Fi access point.
- Add HMAC message signing on nodes and checks in the backend.
- Merge the two web app families into one and retire the older pair.
- Join the two route prefixes (`/api` and `/api/v1`) into one clear scheme.
- Finish the placeholder pages: affected area, alert admin, history, response, audit.

**Later**
- Stronger support for flood, pollution and heat.
- Real fuel, terrain and weather inputs for fire simulation.
- Calibration tools and field accuracy reports.
- User accounts and roles for officials.
- Fill in `docs/architecture/` and `docs/runbooks/`.

---

## Safety and security notes

NexAlert makes safety-related output. Please treat it that way.

- **Keep a human in the loop.** The system recommends. An authorized person approves.
- **Never commit secrets.** That means `.env` files, VAPID private keys (including `.pem` backups), MQTT passwords, database passwords and device secrets. If one was ever committed, rotate it.
- **Use HTTPS** for anything that uses push notifications or service workers outside `localhost`.
- **Lock down MQTT.** Turn on a username and password, and limit who can reach the broker, for anything beyond a trusted test network.
- **Be careful with migrations.** Do not point development migrations at real data.
- **Test for wrong alarms.** Check both false alarms and missed alarms, on real sensors, before anyone relies on this.
- **Calibrate sensors.** Check clocks, offline recovery and delivery tracking on the real hardware.
- **Mark test data.** Use `"source": "SIMULATION"` for anything that is not from a real sensor.

---

## Docs and design rules

- [`docs/implementation/IMPLEMENTATION_CONSTITUTION.md`](docs/implementation/IMPLEMENTATION_CONSTITUTION.md): the rules the code must follow
- [`docs/implementation/REPOSITORY_MAP.md`](docs/implementation/REPOSITORY_MAP.md): who owns which part
- [`docs/implementation/DEVELOPMENT_WORKFLOW.md`](docs/implementation/DEVELOPMENT_WORKFLOW.md): how to plan, build, check and commit
- [`docs/implementation/DECISIONS.md`](docs/implementation/DECISIONS.md): why we chose what we chose
- [`docs/OFFLINE_LOCAL_NETWORK_SETUP.md`](docs/OFFLINE_LOCAL_NETWORK_SETUP.md): hub and Wi-Fi setup
- [`firmware/BUILD_INSTRUCTIONS.md`](firmware/BUILD_INSTRUCTIONS.md): firmware build help
- `docs/specifications/` and `docs/specification_text/`: the original specifications

Core design rules, in short:

1. Missing data is never turned into zero.
2. Measurement time and receive time are different.
3. Hardware data and simulation data are always labeled.
4. Health, quality, reliability, confidence, severity and risk are separate ideas.
5. Confidence and risk are scores, not probabilities.
6. A region can disagree with a node, but never erases the node's own state.
7. A human approves alerts.
8. Each layer keeps working when the layer above it is gone.

---

## Contributing

1. Read the constitution and workflow docs above.
2. Make a small, focused change.
3. If you change a formula or the telemetry contract, update **every** copy (C, Python, TypeScript, schema, golden vectors) and run all the tests.
4. Say clearly in your pull request what you tested, and what you did **not** test.
5. Do not mark a feature as verified until it has been run, not just written.

---

**NexAlert**: early warning that keeps working when things go wrong.

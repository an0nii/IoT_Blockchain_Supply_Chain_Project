# IoT Blockchain Supply Chain

A supply chain management platform built on **Hyperledger Fabric**. IoT devices on Raspberry Pi scan dual-layer QR codes and record shipment events on-chain. A web dashboard handles device registration, QR generation, and label tracking.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌────────────────────────┐
│  Vue.js     │────>│  Flask Backend   │────>│  PostgreSQL            │
│  :8080      │     │  :3000           │     │  (devices, keys)       │
└─────────────┘     └──────────────────┘     └────────────────────────┘
       │
       │             ┌──────────────────┐
       └────────────>│ Blockchain GW    │──┐
                     │ (Go) :3001       │  │
                     └──────────────────┘  │   ┌─────────────────────┐
                                           └──>│  Hyperledger Fabric │
┌─────────────┐     ┌──────────────────┐  ┌──> │  (iot-supply-chain) │
│ Raspberry Pi│────>│  IoT Gateway     │──┘    └─────────────────────┘
│ (picamera2) │     │ (Go) :3002       │
└─────────────┘     └──────────────────┘
```

**Services:**
| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 8080 | Vue.js 3 dashboard |
| `backend` | 3000 | Flask — device registry, QR generation |
| `blockchain-gateway` | 3001 | Go — dashboard → Fabric (admin identity) |
| `gateway` | 3002 | Go — IoT devices → Fabric (per-device identity) |
| `postgres` | — | Device and key storage |

## QR Code Format

Each label carries a **dual-layer QR code** — two QR matrices encoded into a single image using cross-pattern superposition:
- **Layer 1:** `base64(zlib(labelId||sender||receiver))` — compressed payload
- **Layer 2:** ECDSA-SHA256 signature of Layer 1 (SECP256k1)

The IoT device decodes both layers on-device using OpenCV.

## Prerequisites

- Docker & Docker Compose
- Go 1.23+ (for local development)
- Hyperledger Fabric binaries (`fabric-samples/test-network`)

## Quick Start

### 1. Clone with submodules

```bash
git clone --recurse-submodules <repo-url>
cd IoT_Blockchain_Supply_Chain_Project
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env - set ADMIN_API_KEY, SENDER_API_KEY, RECEIVER_API_KEY
```

### 3. Configure IoT devices

```bash
cp gateway/devices.example.json gateway/devices.json
# Edit gateway/devices.json - add device certificates and API keys
```

### 4. Start Fabric network and deploy chaincode

```bash
chmod +x start.sh
./start.sh
```

This will:
1. Bring up the Fabric `test-network` with a CA
2. Deploy the `iot-supply-chain` chaincode
3. Start the IoT Gateway container
4. Print next steps

### 5. Start the full stack

```bash
docker compose up -d
```

### 6. Initialize the contract owner (once)

```bash
source .env
curl -s -X POST http://localhost:3002/api/admin/init \
  -H "X-Admin-Key: $ADMIN_API_KEY"
```

The dashboard is available at `http://localhost:8080`.

## IoT Device (Raspberry Pi 5)

The scanner runs on a Raspberry Pi 5 with a camera module:

```bash
export GATEWAY_URL=http://<host-ip>:3002
export DEVICE_API_KEY=<key from devices.json>
export DEVICE_ROLE=sender   # or: receiver

# Native
python IoT_device/qr_scanning_and_sending/main.py

# Docker (balenalib/raspberrypi5 base)
docker build -t iot-scanner ./IoT_device/qr_scanning_and_sending
docker run --device /dev/video0 \
  -e GATEWAY_URL -e DEVICE_API_KEY -e DEVICE_ROLE \
  iot-scanner
```

## API Reference

### Flask Backend `:3000`
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/devices` | List registered devices |
| `POST` | `/api/devices` | Register a device |
| `POST` | `/api/generate_qr` | Generate dual-layer QR |
| `POST` | `/api/generate_keys` | Generate ECDSA keypair |

### IoT Gateway `:3002`
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/admin/init` | Admin | Initialize contract owner |
| `POST` | `/api/admin/authorize-device` | Admin | Authorize IoT device on-chain |
| `POST` | `/api/admin/authorize-label-creator` | Admin | Authorize label creator |
| `POST` | `/api/labels` | Device | Create label |
| `POST` | `/api/labels/{id}/mark-sent` | Device | Mark label as sent |
| `POST` | `/api/labels/{id}/mark-received` | Device | Mark label as received |
| `GET` | `/api/labels/{id}` | Device | Get label |

### Blockchain Gateway `:3001`
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/blockchain/labels` | Create label via admin identity |
| `GET` | `/api/blockchain/labels` | List all labels |
| `GET` | `/api/blockchain/labels/{id}` | Get label |
| `POST` | `/api/blockchain/labels/{id}/sent` | Mark as sent |
| `POST` | `/api/blockchain/labels/{id}/received` | Mark as received |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vue.js 3, Vue Router, Tailwind CSS, Axios |
| Backend | Python 3.11, Flask, SQLAlchemy, OpenCV, ecdsa |
| Gateways | Go 1.23, Hyperledger Fabric Gateway SDK |
| Blockchain | Hyperledger Fabric 2.x, Go chaincode |
| Database | PostgreSQL 16 |
| IoT | Raspberry Pi 5, picamera2, OpenCV |
| Infra | Docker Compose |

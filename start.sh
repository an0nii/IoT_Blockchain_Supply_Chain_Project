set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NETWORK_DIR="$SCRIPT_DIR/fabric-iot/fabric-samples/test-network"
CHAINCODE_PATH="$SCRIPT_DIR/fabric-iot/fabric-samples/hyperledger"

echo ">>> Запуск Fabric test-network..."
cd "$NETWORK_DIR"

./network.sh up createChannel -c mychannel -ca

echo ">>> Деплой чейнкода..."

./network.sh deployCC \
  -ccn iot-supply-chain \
  -ccp "$CHAINCODE_PATH" \
  -ccl go

cd "$SCRIPT_DIR"

if [ ! -f .env ]; then
  echo ">>> Файл .env не найден, копирую из .env.example"
  cp .env.example .env
  echo "[!!!] ADMIN_API_KEY, SENDER_API_KEY, RECEIVER_API_KEY не заданы"
  exit 1
fi

if [ ! -f gateway/devices.json ]; then
  echo "[!!!] Файл gateway/devices.json не найден."
  exit 1
fi

echo ">>> Запуск Gateway..."
docker compose up -d gateway

echo ""
echo "=== Gateway запущен! ==="
echo ""

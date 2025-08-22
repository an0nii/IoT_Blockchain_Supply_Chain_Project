# IoT Blockchain Supply Chain Project

This project is a web platform for supply chain management using modern frontend, backend and blockchain technologies. The application allows you to:
- Add IoT devices with registration in the blockchain via MetaMask and a smart contract.
- View the list of devices and their detailed data.
- Get information about products associated with devices.
- Generate tags and QR codes for products.
- Connect a wallet via the vue-connect-wallet library on the frontend.

## Installation and launch

### Backend

1. Go to the `backend` directory:
```bash
cd .../IoT_Blockchain_CW/backend
```
2. Create and activate a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate
```
3. Install dependencies:
```bash
pip install -r requirments.txt
```
4. Start the server:
```bash
python server.py
```
The server will be available at `http://localhost:3000`.

### Frontend

1. Go to the `frontend` directory:
```bash
cd .../IoT_Blockchain_CW/frontend
```
2. Install npm dependencies:
```bash
npm install
```
3. Run the project in development mode:
```bash
npm run serve
```
The application will be launched, and you can open it in the browser at the address specified in the terminal (usually `http://localhost:8080`).

## Technologies used

- **Frontend:**
- Vue.js and Vue Router for creating single-page applications.
- Tailwind CSS for quick styling and creating a responsive interface.
- vue-connect-wallet for integrating MetaMask into the interface.
- ethers.js for interacting with the Ethereum network and smart contracts.

- **Backend:**
- Flask with flask-cors for creating RESTful API.
- pyqrcode, pypng, zlib, base64 for generating and processing QR codes.

- **Blockchain:**
- Smart contract (IOTContractMonitoring) for device authorization and tag management.

## Future plans

- **State management migration:** Consider using Pinia for centralized application state management instead of localStorage/sessionStorage.
- **UI improvements:** Refining the design and improving usability.
- **Backend optimizations:** Error handling, performance improvements, and server-side scaling.
- **Integration with backend databases:** Switching to a more reliable data storage for user sharing and better security.

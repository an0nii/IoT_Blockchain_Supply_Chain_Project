import requests
import logging

logger = logging.getLogger(__name__)


class GatewaySender:
    def __init__(self, gateway_url: str, device_api_key: str):
        self.gateway_url = gateway_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers['X-Device-Key'] = device_api_key

    def mark_as_sent(self, label_id: str) -> dict:
        resp = self.session.post(f"{self.gateway_url}/api/labels/{label_id}/mark-sent")
        resp.raise_for_status()
        return resp.json()

    def mark_as_received(self, label_id: str) -> dict:
        resp = self.session.post(f"{self.gateway_url}/api/labels/{label_id}/mark-received")
        resp.raise_for_status()
        return resp.json()

    def get_label(self, label_id: str) -> dict:
        resp = self.session.get(f"{self.gateway_url}/api/labels/{label_id}")
        resp.raise_for_status()
        return resp.json()

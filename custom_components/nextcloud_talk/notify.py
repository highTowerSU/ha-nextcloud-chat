import logging
import os
from typing import Any, Dict, List, Optional

import requests
import voluptuous as vol

from homeassistant.components.notify import (
    PLATFORM_SCHEMA, BaseNotificationService
)
from homeassistant.const import CONF_API_KEY, CONF_URL
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_CHAT_ID = "chat_id"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.url,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_CHAT_ID): cv.string,
})

def get_service(hass, config, discovery_info=None):
    """Get the Nextcloud Talk notification service."""
    url = config[CONF_URL]
    api_key = config[CONF_API_KEY]
    chat_id = config[CONF_CHAT_ID]

    return NextcloudTalkNotificationService(hass, url, api_key, chat_id)

class NextcloudTalkNotificationService(BaseNotificationService):
    """Implement the notification service for Nextcloud Talk."""

    def __init__(self, hass, url, api_key, chat_id):
        """Initialize the service."""
        self.hass = hass
        self._url = url
        self._api_key = api_key
        self._chat_id = chat_id

    def send_message(self, message="", **kwargs):
        """Send a message to a Nextcloud Talk chat."""
        data = kwargs.get("data") or {}

        attachments = self._gather_attachments(data)
        for attachment in attachments:
            self._send_attachment(attachment)

        if message:
            response = requests.post(
                f"{self._url}/ocs/v2.php/apps/spreed/api/v1/chat/{self._chat_id}",
                json={"token": self._chat_id, "message": message},
                headers=self._build_headers(),
            )

            if response.status_code != 201:
                _LOGGER.error("Failed to send message: %s", response.text)

    def _build_headers(self, content_type: Optional[str] = "application/json") -> Dict[str, str]:
        headers = {
            "Authorization": f"Basic {self._api_key}",
            "OCS-APIRequest": "true",
            "Accept": "application/json",
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _gather_attachments(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        attachments: List[Dict[str, Any]] = []
        for key in ("photo", "video", "file"):
            if key not in data:
                continue
            items = data[key]
            if not isinstance(items, list):
                items = [items]
            for item in items:
                if isinstance(item, dict):
                    file_path = item.get("file")
                    caption = item.get("caption")
                else:
                    file_path = item
                    caption = None
                if not file_path:
                    _LOGGER.warning("Attachment entry without file for key '%s'", key)
                    continue
                attachments.append({"path": file_path, "caption": caption})
        return attachments

    def _resolve_path(self, path: str) -> str:
        if os.path.isabs(path):
            return path
        return self.hass.config.path(path)

    def _send_attachment(self, attachment: Dict[str, Any]) -> None:
        path = self._resolve_path(attachment["path"])
        caption = attachment.get("caption")

        if not os.path.isfile(path):
            _LOGGER.error("Attachment file not found: %s", path)
            return

        try:
            with open(path, "rb") as file_handle:
                files = {"file": (os.path.basename(path), file_handle)}
                form_data: Dict[str, Any] = {}
                if caption:
                    form_data["message"] = caption

                response = requests.post(
                    f"{self._url}/ocs/v2.php/apps/spreed/api/v4/room/{self._chat_id}/files",
                    headers=self._build_headers(content_type=None),
                    files=files,
                    data=form_data,
                )
        except OSError as err:
            _LOGGER.error("Failed to open attachment %s: %s", path, err)
            return

        if response.status_code != 201:
            _LOGGER.error("Failed to upload attachment %s: %s", path, response.text)

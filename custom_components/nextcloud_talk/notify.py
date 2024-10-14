import logging
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

    return NextcloudTalkNotificationService(url, api_key, chat_id)

class NextcloudTalkNotificationService(BaseNotificationService):
    """Implement the notification service for Nextcloud Talk."""

    def __init__(self, url, api_key, chat_id):
        """Initialize the service."""
        self._url = url
        self._api_key = api_key
        self._chat_id = chat_id

    def send_message(self, message="", **kwargs):
        """Send a message to a Nextcloud Talk chat."""
        payload = {
            "token": self._chat_id,
            "message": message
        }
        headers = {
            "Authorization": f"Basic {self._api_key}",
            "OCS-APIRequest": "true",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self._url}/ocs/v2.php/apps/spreed/api/v1/chat/{self._chat_id}",
            json=payload,
            headers=headers
        )

        if response.status_code != 201:
            _LOGGER.error("Failed to send message: %s", response.text)

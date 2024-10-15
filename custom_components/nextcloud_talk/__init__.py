"""Nextcloud Talk Custom Component for Home Assistant."""
from homeassistant.components.webhook import async_register, async_unregister
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Nextcloud Talk from a config entry."""
    config = entry.data

    # Register the webhook
    async_register(
        hass, DOMAIN, "Nextcloud Talk", entry.entry_id, handle_webhook
    )

    # Log the URL and other config details
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "url": config.get("url"),
        "api_key": config.get("api_key"),
        "chat_id": config.get("chat_id"),
    }

    return True

async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove a config entry."""
    async_unregister(hass, entry.entry_id)
    hass.data[DOMAIN].pop(entry.entry_id)
    return True

async def handle_webhook(hass, webhook_id, request):
    """Handle incoming Nextcloud Talk messages."""
    payload = await request.json()

    message = payload.get("message", None)
    if message:
        # Fire an event for the incoming message
        hass.bus.fire("nextcloud_talk_message", {
            "message": message,
            "sender": payload.get("actorDisplayName", "Unknown")
        })

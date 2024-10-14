"""Nextcloud Talk Custom Component for Home Assistant."""
from homeassistant.components.webhook import async_register, async_unregister

DOMAIN = "nextcloud_talk"

async def async_setup_entry(hass, entry):
    """Set up Nextcloud Talk from a config entry."""

    # Register the webhook
    async_register(
        hass, DOMAIN, "Nextcloud Talk", entry.data["webhook_id"], handle_webhook
    )

async def async_remove_entry(hass, entry):
    """Remove a config entry."""
    async_unregister(hass, entry.data["webhook_id"])

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

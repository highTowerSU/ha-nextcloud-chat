"""Nextcloud Talk Custom Component for Home Assistant."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Nextcloud Talk using the API token."""

    # Retrieve the API token from the config entry
    api_token = entry.data.get("api_token")

    # Example: Use the API token for making authenticated requests to Nextcloud
    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api_token": api_token
    }

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle unloading of a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id)
    return True

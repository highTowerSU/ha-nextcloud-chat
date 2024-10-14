from homeassistant import config_entries
import voluptuous as vol

from .const import DOMAIN

@config_entries.HANDLERS.register(DOMAIN)
class NextcloudTalkFlowHandler(config_entries.ConfigFlow):
    """Handle a Nextcloud Talk config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required("url"): str,
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                })
            )

        return self.async_create_entry(
            title="Nextcloud Talk",
            data={
                "url": user_input["url"],
                "username": user_input["username"],
                "password": user_input["password"],
            }
        )

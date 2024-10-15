import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import aiohttp
from .const import DOMAIN

LOGIN_POLL_INTERVAL = 5  # Poll every 5 seconds

# Function to start Nextcloud Login Flow v2 using aiohttp for async requests
async def start_login_flow(base_url, session):
    login_url = f"{base_url}/index.php/login/v2"
    async with session.post(login_url) as response:
        if response.status == 200:
            return await response.json()  # Returns the 'poll' and 'login' URLs
    return None

# Function to poll for the authentication token using aiohttp for async requests
async def poll_for_token(poll_url, session):
    while True:
        async with session.get(poll_url) as response:
            if response.status == 200:
                result = await response.json()
                if result.get("token"):
                    return result.get("token")
        await asyncio.sleep(LOGIN_POLL_INTERVAL)

class NextcloudTalkConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nextcloud Talk."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            base_url = user_input["url"]

            # Start Login Flow v2 using aiohttp session
            async with aiohttp.ClientSession() as session:
                login_data = await start_login_flow(base_url, session)
                if login_data:
                    login_url = login_data["login"]
                    poll_url = login_data["poll"]
                    
                    # Save the poll URL in hass.data for later use
                    self.hass.data[DOMAIN] = {"poll_url": poll_url}

                    # Show the login URL to the user
                    return self.async_external_step(url=login_url)
                else:
                    errors["base"] = "auth_failed"

        # Schema for user to input Nextcloud URL
        data_schema = vol.Schema({
            vol.Required("url"): str
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_external(self, user_input=None):
        """Handle the external callback once the user has logged in."""
        poll_url = self.hass.data[DOMAIN]["poll_url"]

        # Poll for the token using aiohttp session
        async with aiohttp.ClientSession() as session:
            api_token = await poll_for_token(poll_url, session)

            if api_token:
                # Store the API token and complete the config flow
                return self.async_create_entry(
                    title="Nextcloud Talk",
                    data={"api_token": api_token}
                )

        return self.async_abort(reason="auth_failed")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Handle options flow."""
        return OptionsFlowHandler(config_entry)

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import aiohttp
import asyncio
import logging
from .const import DOMAIN

LOGIN_POLL_INTERVAL = 5  # Poll every 5 seconds
_LOGGER = logging.getLogger(__name__)

# Function to start Nextcloud Login Flow v2 using aiohttp for async requests
async def start_login_flow(base_url, session):
    login_url = f"{base_url}/index.php/login/v2"
    _LOGGER.debug("Starting Nextcloud login flow with URL: %s", login_url)

    async with session.post(login_url) as response:
        _LOGGER.debug("Received response from Nextcloud login flow with status: %s", response.status)
        if response.status == 200:
            json_response = await response.json()
            _LOGGER.debug("Full response from Nextcloud login flow: %s", json_response)
            return json_response  # Returns the 'poll' and 'login' URLs
    return None

# Function to poll for the authentication token using aiohttp for async requests
async def poll_for_token(poll_url, token, session):
    _LOGGER.debug("Starting polling for token with URL: %s", poll_url)
    timeout = 20  # Set a 1-minute timeout for the polling process
    start_time = asyncio.get_event_loop().time()

    headers = {
        "OCS-APIRequest": "true"
    }

    while True:
        # Check if the timeout has been reached
        if asyncio.get_event_loop().time() - start_time > timeout:
            _LOGGER.error("Polling for token timed out after 1 minute.")
            return None

        # Make a POST request with the token as data
        async with session.post(poll_url, headers=headers, data={"token": token}) as response:
            _LOGGER.debug("Polling response status: %s", response.status)
            if response.status == 200:
                result = await response.json()
                _LOGGER.debug("Polling result: %s", result)
                if result.get("appPassword"):
                    _LOGGER.debug("App password received: %s", result.get("appPassword"))
                    return {
                        "server": result.get("server"),
                        "loginName": result.get("loginName"),
                        "appPassword": result.get("appPassword")
                    }
            elif response.status == 404:
                _LOGGER.debug("Authentication not completed yet. Retrying...")
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
                    login_url = login_data.get("login")
                    poll_data = login_data.get("poll")
                    
                    if poll_data is None or "token" not in poll_data or login_url is None:
                        _LOGGER.error("Token or login URL missing from Nextcloud response.")
                        errors["base"] = "auth_failed"
                    else:
                        token = poll_data["token"]
                        # Construct the polling URL with the static endpoint and the token
                        poll_url = f"{poll_data['endpoint']}?token={token}"
                        
                        # Save the poll URL and token in hass.data for later use
                        self.hass.data[DOMAIN] = {"poll_url": poll_url, "token": token}
                        _LOGGER.debug("Poll URL saved: %s", poll_url)

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
        poll_url = self.hass.data[DOMAIN].get("poll_url")
        token = self.hass.data[DOMAIN].get("token")

        if not poll_url or not token:
            _LOGGER.error("Poll URL or token is not set. Aborting.")
            return self.async_abort(reason="poll_url_not_set")

        _LOGGER.debug("Polling for token with URL: %s", poll_url)

        async with aiohttp.ClientSession() as session:
            credentials = await poll_for_token(poll_url, token, session)

            if credentials:
                # Store the credentials and complete the config flow
                return self.async_create_entry(
                    title="Nextcloud Talk",
                    data=credentials
                )

        _LOGGER.error("Failed to retrieve credentials. Aborting.")
        return self.async_abort(reason="auth_failed")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Handle options flow."""
        return OptionsFlowHandler(config_entry)

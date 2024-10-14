# Nextcloud Talk Custom Component for Home Assistant

This is a custom component for [Home Assistant](https://www.home-assistant.io) that allows sending and receiving messages through [Nextcloud Talk](https://nextcloud.com/talk/).

## Features

- Send messages to Nextcloud Talk channels using the Nextcloud OCS API.
- Receive messages from Nextcloud Talk via webhooks, and trigger Home Assistant automations based on those messages.
- Simple configuration and setup via Home Assistant UI.

## Installation

1. **Download the custom component:**
   Clone this repository or download it as a ZIP file and place it in the `custom_components/nextcloud_talk` directory inside your Home Assistant configuration folder.

   ```bash
   git clone git@github.com:highTowerSU/ha-nextcloud-chat.git
   ```

2. **Ensure the directory structure looks like this:**

   ```
   custom_components/
   └── nextcloud_talk
       ├── __init__.py
       ├── manifest.json
       ├── notify.py
       ├── auth_flow.py
       └── services.yaml
   ```

3. **Restart Home Assistant:**
   After placing the files in the correct directory, restart Home Assistant to load the custom component.

## Configuration

Once the component is installed, you can configure it either via the UI (if using `auth_flow.py`), or by adding the following to your `configuration.yaml`:

```yaml
notify:
  - platform: nextcloud_talk
    url: "https://your-nextcloud-instance.com"
    api_key: "Base64-encoded-auth-string"
    chat_id: "your_conversation_id"
```

### Parameters

- **url**: The URL of your Nextcloud instance (e.g., https://nextcloud.example.com).
- **api_key**: Your Base64-encoded authentication credentials (`username:password` encoded in Base64).
- **chat_id**: The 'conversation_id' of the Nextcloud Talk chat where messages should be sent.

## Sending Messages

Once configured, you can use the `notify` service in Home Assistant to send messages to a Nextcloud Talk channel. Example:

```yaml
service: notify.nextcloud_talk
data:
  message: "This is a message sent to Nextcloud Talk from Home Assistant."
```

## Receiving Messages

Messages sent to the Nextcloud Talk channel will trigger the webhook registered by this component. You can create automations in Home Assistant based on received messages:

```yaml
automation:
  - alias: "React to Nextcloud Talk Message"
    trigger:
      platform: event
      event_type: nextcloud_talk_message
    action:
      service: notify.persistent_notification
      data_template:
        title: "New Message from Nextcloud Talk"
        message: "{{ trigger.event.data.sender }}: {{ trigger.event.data.message }}"
``

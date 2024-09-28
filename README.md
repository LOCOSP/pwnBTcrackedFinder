# Bluetooth Notifier Plugin for Pwnagotchi

## Description
The `BluetoothNotifier` is a custom plugin for the Pwnagotchi platform, designed to notify a specified device via Bluetooth when a matching Wi-Fi network is found. This plugin scans networks based on the entries in a `wpa-sec.cracked.potfile` and sends a message to a target device using its Bluetooth MAC address.

## Features
- Monitors Wi-Fi networks detected by the Pwnagotchi.
- Compares detected networks against entries in `wpa-sec.cracked.potfile`.
- Sends a notification via Bluetooth to a specified device (e.g., a mobile phone) when a matching network is found.
- Configurable target device and Bluetooth port through `config.toml`.

## Prerequisites
Before using this plugin, ensure that your Pwnagotchi has the following:
1. **Bluetooth support** enabled.
2. The file `/root/handshakes/wpa-sec.cracked.potfile` present and populated with entries in the following format: `hash:bssid:ssid`

Where:
- `hash` – Wi-Fi password hash.
- `bssid` – MAC address of the network.
- `ssid` – Network name.
- `password` – Password for the network (optional).

## Installation
1. Download the plugin file `bluetooth_notifier.py` and place it in the Pwnagotchi plugin directory (usually `/usr/local/share/pwnagotchi/plugins/`):
```bash
sudo wget -O /usr/local/share/pwnagotchi/plugins/bluetooth_notifier.py https://example.com/bluetooth_notifier.py

2. Edit your Pwnagotchi configuration file (/etc/pwnagotchi/config.toml) to enable and configure the plugin:

```toml
main.plugins.bluetooth_notifier.enabled = true
main.plugins.bluetooth_notifier.target_mac_address = "XX:XX:XX:XX:XX:XX"  # Adres MAC telefonu docelowego
main.plugins.bluetooth_notifier.bluetooth_port = 1  # Domyślny port Bluetooth RFCOMM
```
3. Restart the Pwnagotchi to apply the changes:

```sudo systemctl restart pwnagotchi```

or

```pwnkill```

## How It Works
Initialization: When the plugin is loaded, it reads the specified configuration parameters from config.toml.
Monitoring Networks: During the channel switch events (on_channel_switch), it scans all visible access points (APs).

Matching Networks: If any detected network's BSSID or SSID matches the entries in wpa-sec.cracked.potfile, the plugin sends a notification to the specified Bluetooth device.
Bluetooth Notification: The plugin establishes an RFCOMM connection and sends the SSID and BSSID of the detected network to the target device.

## Troubleshooting
Plugin not loading: Make sure the config.toml file has been properly edited and the plugin is enabled.
Bluetooth errors: Verify that the target MAC address is correct and that the Bluetooth module is functioning correctly on your Pwnagotchi.
Missing potfile: Ensure that the file wpa-sec.cracked.potfile exists at `/root/handshakes/` and is properly formatted.
## License
This plugin is licensed under the GPL3 License. See LICENSE for more details.

## Contributing
If you'd like to contribute to this project, feel free to fork the repository and submit a pull request. Any improvements, bug fixes, or feature additions are welcome!
# Bluetooth Notifier Plugin for Pwnagotchi

## Description
The `BluetoothNotifier` is a custom plugin for the Pwnagotchi platform, designed to notify a specified device via Bluetooth when a matching Wi-Fi network is found. This plugin scans networks based on the entries in a `wpa-sec.cracked.potfile` and sends a message to a target device using its Bluetooth MAC address.

## Features
- Monitors Wi-Fi networks detected by the Pwnagotchi.
- Compares detected networks against entries in `wpa-sec.cracked.potfile`.
- Sends a notification via Blu
import logging
import os
import bluetooth
from pwnagotchi import plugins

class BluetoothNotifier(plugins.Plugin):
    __author__ = 'twojemail@gmail.com'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'Notifies via Bluetooth when a matching network is found based on wpa-sec.cracked.potfile.'

    def __init__(self):
        self.ready = False
        self.potfile_path = "/root/handshakes/wpa-sec.cracked.potfile"
        self.target_bssid = []
        self.target_ssid = []
        self.target_mac_address = None
        self.bluetooth_port = None

    def on_config_changed(self, config):
        self.config = config
        # Wczytanie parametrów z pliku config.toml
        self.target_mac_address = config['main']['plugins']['bluetooth_notifier'].get('target_mac_address', None)
        self.bluetooth_port = config['main']['plugins']['bluetooth_notifier'].get('bluetooth_port', 1)

        if not self.target_mac_address:
            logging.error("BluetoothNotifier: Nie ustawiono adresu MAC docelowego w config.toml. Wyłączam plugin.")
            return

        logging.info(f"BluetoothNotifier: Używam adresu MAC {self.target_mac_address} i portu {self.bluetooth_port}")

    def on_ready(self, agent):
        # Wczytaj BSSID i SSID z pliku `wpa-sec.cracked.potfile`
        if os.path.exists(self.potfile_path):
            with open(self.potfile_path, 'r') as potfile:
                lines = potfile.readlines()
                for line in lines:
                    # Zakładamy, że plik ma format: hash:bssid:ssid:hasło
                    parts = line.split(":")
                    if len(parts) >= 3:
                        self.target_bssid.append(parts[1].lower())
                        self.target_ssid.append(parts[2].strip())
            logging.info("BluetoothNotifier: Wczytano sieci docelowe z wpa-sec.cracked.potfile")
            self.ready = True
        else:
            logging.error(f"BluetoothNotifier: Nie znaleziono pliku {self.potfile_path}. Plugin nie będzie działał.")

    def on_channel_switch(self, agent, channel):
        if not self.ready:
            return

        logging.info(f"BluetoothNotifier: Przełączono na kanał {channel}. Skanowanie sieci...")

        # Sprawdzenie wykrytych sieci
        for ap in agent.recon.aps:
            bssid = ap['mac'].lower()
            ssid = ap['hostname'].strip()
            
            # Sprawdzenie, czy sieć jest na liście docelowej
            if bssid in self.target_bssid or ssid in self.target_ssid:
                message = f"Znaleziono pasującą sieć! SSID: {ssid}, BSSID: {bssid}"
                logging.info(f"BluetoothNotifier: {message}")
                self.send_bluetooth_notification(message)
                break  # Zatrzymanie po znalezieniu jednej pasującej sieci

    def send_bluetooth_notification(self, message):
        try:
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((self.target_mac_address, self.bluetooth_port))
            sock.send(message)
            sock.close()
            logging.info(f"BluetoothNotifier: Wysłano powiadomienie Bluetooth: {message}")
        except Exception as e:
            logging.error(f"BluetoothNotifier: Błąd przy wysyłaniu powiadomienia Bluetooth: {e}")

    def on_unload(self, ui):
        self.ready = False
        logging.info("BluetoothNotifier: Plugin wyłączony")

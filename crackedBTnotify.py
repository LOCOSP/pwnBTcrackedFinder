import logging
import os
import dbus

import pwnagotchi.plugins as plugins

class BTError(Exception):
    """
    Custom bluetooth exception
    """
    pass

class BTNap:
    """
    This class creates a bluetooth connection to the specified bt-mac
    """

    IFACE_BASE = 'org.bluez'
    IFACE_DEV = 'org.bluez.Device1'
    IFACE_ADAPTER = 'org.bluez.Adapter1'
    IFACE_PROPS = 'org.freedesktop.DBus.Properties'

    def __init__(self, mac):
        self._mac = mac

    @staticmethod
    def get_bus():
        """
        Get systembus obj
        """
        bus = getattr(BTNap.get_bus, 'cached_obj', None)
        if not bus:
            bus = BTNap.get_bus.cached_obj = dbus.SystemBus()
        return bus

    @staticmethod
    def get_manager():
        """
        Get manager obj
        """
        manager = getattr(BTNap.get_manager, 'cached_obj', None)
        if not manager:
            manager = BTNap.get_manager.cached_obj = dbus.Interface(
                BTNap.get_bus().get_object(BTNap.IFACE_BASE, '/'),
                'org.freedesktop.DBus.ObjectManager')
        return manager

    @staticmethod
    def prop_get(obj, k, iface=None):
        """
        Get a property of the obj
        """
        if iface is None:
            iface = obj.dbus_interface
        return obj.Get(iface, k, dbus_interface=BTNap.IFACE_PROPS)

    @staticmethod
    def prop_set(obj, k, v, iface=None):
        """
        Set a property of the obj
        """
        if iface is None:
            iface = obj.dbus_interface
        return obj.Set(iface, k, v, dbus_interface=BTNap.IFACE_PROPS)

    @staticmethod
    def find_adapter(pattern=None):
        """
        Find the bt adapter
        """
        return BTNap.find_adapter_in_objects(BTNap.get_manager().GetManagedObjects(), pattern)

    @staticmethod
    def find_adapter_in_objects(objects, pattern=None):
        """
        Finds the obj with a pattern
        """
        bus, obj = BTNap.get_bus(), None
        for path, ifaces in objects.items():
            adapter = ifaces.get(BTNap.IFACE_ADAPTER)
            if adapter is None:
                continue
            if not pattern or pattern == adapter['Address'] or path.endswith(pattern):
                obj = bus.get_object(BTNap.IFACE_BASE, path)
                yield dbus.Interface(obj, BTNap.IFACE_ADAPTER)
        if obj is None:
            raise BTError('Bluetooth adapter not found')

    @staticmethod
    def find_device(device_address, adapter_pattern=None):
        """
        Finds the device
        """
        return BTNap.find_device_in_objects(BTNap.get_manager().GetManagedObjects(),
                                            device_address, adapter_pattern)

    @staticmethod
    def find_device_in_objects(objects, device_address, adapter_pattern=None):
        """
        Finds the device in objects
        """
        bus = BTNap.get_bus()
        path_prefix = ''
        if adapter_pattern:
            if not isinstance(adapter_pattern, str):
                adapter = adapter_pattern
            else:
                adapter = BTNap.find_adapter_in_objects(objects, adapter_pattern)
            path_prefix = adapter.object_path
        for path, ifaces in objects.items():
            device = ifaces.get(BTNap.IFACE_DEV)
            if device is None:
                continue
            if str(device['Address']).lower() == device_address.lower() and path.startswith(path_prefix):
                obj = bus.get_object(BTNap.IFACE_BASE, path)
                return dbus.Interface(obj, BTNap.IFACE_DEV)
        raise BTError('Bluetooth device not found')

    def power(self, on=True):
        """
        Set power of devices to on/off
        """
        logging.debug("BT-TETHER: Changing bluetooth device to %s", str(on))

        try:
            devs = list(BTNap.find_adapter())
            devs = dict((BTNap.prop_get(dev, 'Address'), dev) for dev in devs)
        except BTError as bt_err:
            logging.error(bt_err)
            return None

        for dev_addr, dev in devs.items():
            BTNap.prop_set(dev, 'Powered', on)
            logging.debug('Set power of %s (addr %s) to %s', dev.object_path, dev_addr, str(on))

        if devs:
            return list(devs.values())[0]

        return None

    def is_paired(self):
        """
        Check if already connected
        """
        logging.debug("BT-TETHER: Checking if device is paired")

        bt_dev = self.power(True)

        if not bt_dev:
            logging.debug("BT-TETHER: No bluetooth device found.")
            return False

        try:
            dev_remote = BTNap.find_device(self._mac, bt_dev)
            return bool(BTNap.prop_get(dev_remote, 'Paired'))
        except BTError:
            logging.debug("BT-TETHER: Device is not paired.")
        return False

    def wait_for_device(self, timeout=15):
        """
        Wait for device

        returns device if found None if not
        """
        logging.debug("BT-TETHER: Waiting for device")

        bt_dev = self.power(True)

        if not bt_dev:
            logging.debug("BT-TETHER: No bluetooth device found.")
            return None

        try:
            logging.debug("BT-TETHER: Starting discovery ...")
            bt_dev.StartDiscovery()
        except Exception as bt_ex:
            logging.error(bt_ex)
            raise bt_ex

        dev_remote = None

        # could be set to 0, so check if > -1
        while timeout > -1:
            try:
                dev_remote = BTNap.find_device(self._mac, bt_dev)
                logging.debug("BT-TETHER: Using remote device (addr: %s): %s",
                              BTNap.prop_get(dev_remote, 'Address'), dev_remote.object_path)
                break
            except BTError:
                logging.debug("BT-TETHER: Not found yet ...")

            timeout -= 1

        try:
            logging.debug("BT-TETHER: Stopping Discovery ...")
            bt_dev.StopDiscovery()
        except Exception as bt_ex:
            logging.error(bt_ex)
            raise bt_ex

        return dev_remote

    @staticmethod
    def pair(device):
        logging.debug('BT-TETHER: Trying to pair ...')
        try:
            device.Pair()
            logging.debug('BT-TETHER: Successful paired with device ;)')
            return True
        except dbus.exceptions.DBusException as err:
            if err.get_dbus_name() == 'org.bluez.Error.AlreadyExists':
                logging.debug('BT-TETHER: Already paired ...')
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def send_message(device, message):
        logging.debug('BT-TETHER: Trying to send message ...')
        try:
            device.SendMessage(message)
            logging.debug('BT-TETHER: Message sent successfully.')
            return True
        except Exception as e:
            logging.error(f"BT-TETHER: Error sending message: {e}")
            return False

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
        self.bt_manager = None  # Variable for the BTNap instance

    def on_config_changed(self, config):
        self.config = config
        # Load parameters from config.toml
        self.target_mac_address = config['main']['plugins']['bluetooth_notifier'].get('target_mac_address', None)

        if not self.target_mac_address:
            logging.error("BluetoothNotifier: Target MAC address not set in config.toml. Disabling plugin.")
            return

        logging.info(f"BluetoothNotifier: Using MAC address {self.target_mac_address}")

    def on_ready(self, agent):
        # Load BSSID and SSID from the `wpa-sec.cracked.potfile`
        if os.path.exists(self.potfile_path):
            with open(self.potfile_path, 'r') as potfile:
                lines = potfile.readlines()
                for line in lines:
                    # Assuming the file format is: hash:bssid:ssid:password
                    parts = line.split(":")
                    if len(parts) >= 3:
                        self.target_bssid.append(parts[1].lower())
                        self.target_ssid.append(parts[2].strip())
            logging.info("BluetoothNotifier: Loaded target networks from wpa-sec.cracked.potfile")
            self.ready = True
        else:
            logging.error(f"BluetoothNotifier: File {self.potfile_path} not found. Plugin will not work.")
        
        # Initialize BTNap
        self.bt_manager = BTNap(self.target_mac_address)

        if not self.bt_manager.power(True):
            logging.error("BluetoothNotifier: Bluetooth adapter is not available.")
            return

    def on_channel_switch(self, agent, channel):
        if not self.ready:
            return

        logging.info(f"BluetoothNotifier: Channel switched to {channel}")

        # Wait for device to become discoverable
        device = self.bt_manager.wait_for_device()
        if device:
            if self.bt_manager.is_paired():
                logging.info("BluetoothNotifier: Device is already paired.")
            else:
                if self.bt_manager.pair(device):
                    logging.info("BluetoothNotifier: Device paired successfully.")

            message = f"Matching network found! BSSID: {self.target_bssid} SSID: {self.target_ssid}"
            self.bt_manager.send_message(device, message)
        else:
            logging.error("BluetoothNotifier: Device not found.")


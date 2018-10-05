#!/usr/bin/env python3

# Tool to read weight measurement data from Trisa Body Analyze 4.0,
# a smart scale that connects through Bluetooth 4.0 BLE.

# This script uses the `gatt` package to use Bluetooth GATT.
# Get it from: https://github.com/getsenic/gatt-python and add it to PYTHONPATH.

import collections
import enum
import gatt
import struct
import time

ADAPTER = 'hci0'                    # Host's Bluetooth adapter id.
MAC = 'E6:79:32:AB:BA:80'           # Scales's Bluetooth MAC address.
PASSWORD_FILENAME = 'password.txt'  # Stores scale's password.

WEIGHT_SCALE_SERVICE_UUID = '00007802-0000-1000-8000-00805f9b34fb'
MEASUREMENT_CHARACTERISTIC_UUID = '00008a21-0000-1000-8000-00805f9b34fb'
APPEND_MEASUREMENT_CHARACTERISTIC_UUID = '00008a22-0000-1000-8000-00805f9b34fb'  # unused?
DOWNLOAD_COMMAND_CHARACTERISTIC_UUID = '00008a81-0000-1000-8000-00805f9b34fb'
UPLOAD_COMMAND_CHARACTERISTIC_UUID = '00008a82-0000-1000-8000-00805f9b34fb'

# Supposed to be timestamp relative to 2010-01-01 00:00:00. But I think any
# offset can be used. The scale will use this to syncronize its clock.
# Generated with: `date --date='TZ="UTC" 2010-01-01 00:00:00' +%s`
TIMESTAMP_OFFSET = 1262304000

# 4-byte broadcast identifier.
#
# This is set by the host during pairing. Aterwards, the scale will identify
# itself as '01257B' + <hex encoded broadcast id> (so the device name will be
# 14 characters long, in total).
BROADCAST_ID=b'\x01\x02\x03\x04'

class WeightUnit(enum.Enum):
    KILOGRAM = 0
    POUND = 1
    STONE = 2

class MeasurementWeightStatus(enum.Enum):
    UNSTABLE = 0
    STABLE = 1

class MeasurementImpedanceStatus(enum.Enum):
    IDLE = 0
    PROCESSING = 1
    SHOES = 2
    BAREFOOT = 3
    FINISH = 4
    ERROR = 5

WeightScaleMeasurementData = collections.namedtuple(
    'WeightScaleMeasurementData', (
        # int: weight in kilogram (regardless of display unit). Required.
        'weight_kg',
        # WeightUnit: selected unit used for displaying weight. Required.
        'display_unit',
        # int: UNIX timestamp of measurement.
        'timestamp',
        # float: Resistance 1 (used for body composition calculation)
        'resistance1',
        # float: Resistance 2 (used for body composition calculation)
        'resistance2',
        # int: User number (always 0? Maybe it can be changed by the app?)
        'user_number',
        # MeasurementWeightStatus: indicates whether the weight is accurate.
        'measurement_weight_status',
        # MeasurementImpedanceStatus: indicates whether resistances are accurate.
        'measurement_impedance_status',
        # bool: not sure. Probably related to the "append measurement" GATT
        # characteristic, but I don't know what that one does either.
        'has_append_measurement_data',
    ))

def LoadPassword():
    try:
        with open(PASSWORD_FILENAME, 'rt') as password_file:
            try:
                password = bytes.fromhex(password_file.readline().strip())
            except ValueError:
                return None
            if len(password) != 4:
                return None
            return password
    except FileNotFoundError:
        return None

def SavePassword():
    assert password
    with open(PASSWORD_FILENAME, 'wt') as password_file:
        password_file.write(password.hex() + '\n')

def XorBytes(a, b):
    assert len(a) == len(b)
    return bytes(x ^ y for (x, y) in zip(a, b))

def GetUtcCommand():
    return b'\x02' + struct.pack('<i', int(time.time() - TIMESTAMP_OFFSET))

def GetAuthCommand(challenge):
    assert password
    return b'\x20' + XorBytes(challenge, password)

def GetSetBroadcastIdCommand():
    # 0x21 == DOWNLOAD_INFORMATION_BROADCAST_ID_COMMAND
    return b'\x21' + BROADCAST_ID

def GetDisconnectCommand():
    return b'\x22'

def ParseWeightScaleMeasurementData(data):
    def ParseFloatBytes(data):
        assert len(data) == 4
        mantissa, exponent = struct.unpack('<ib', data[0:3] + b'\0' + data[3:4])
        return mantissa * pow(10, exponent)

    def ParseTimestamp(data):
        assert len(data) == 4
        timestamp, = struct.unpack('<i', data)
        return timestamp + TIMESTAMP_OFFSET

    assert len(data) >= 5

    display_unit = (
        WeightUnit.KILOGRAM,
        WeightUnit.STONE,
        WeightUnit.POUND,
        None,
    )[(data[0] & 0x60) >> 5]

    weight_kg = ParseFloatBytes(data[1:5])

    i = 5
    if data[0] & 1:
        assert len(data) >= i + 4
        timestamp = ParseTimestamp(data[i:i + 4])
        i += 4
    else:
        timestamp = None

    if data[0] & 2:
        assert len(data) >= i + 4
        resistance1 = ParseFloatBytes(data[i:i + 4])
        i += 4
    else:
        resistance1 = None

    if data[0] & 4:
        assert len(data) >= i + 4
        resistance2 = ParseFloatBytes(data[i:i + 4])
        i += 4
    else:
        resistance2 = None

    if data[0] & 8:
        user_number = int(data[i])
        i += 1
    else:
        user_number = None

    if data[0] & 16:
        print(i)
        measurement_weight_status = (
            MeasurementWeightStatus.UNSTABLE,
            MeasurementWeightStatus.STABLE,
        )[data[i] & 1]
        measurement_impedance_status = (
            MeasurementImpedanceStatus.IDLE,
            MeasurementImpedanceStatus.PROCESSING,
            MeasurementImpedanceStatus.SHOES,
            MeasurementImpedanceStatus.BAREFOOT,
            MeasurementImpedanceStatus.FINISH,
            MeasurementImpedanceStatus.ERROR,
            None,
            None,
        )[(data[i] & 0xe) >> 1]
        has_append_measurement_data = bool((data[i] & 0x10) >> 4)
        i += 1
    else:
        measurement_weight_status = None
        measurement_impedance_status = None
        has_append_measurement_data = None

    return WeightScaleMeasurementData(
        weight_kg = weight_kg,
        display_unit = display_unit,
        timestamp = timestamp,
        resistance1 = resistance1,
        resistance2 = resistance2,
        user_number = user_number,
        measurement_weight_status = measurement_weight_status,
        measurement_impedance_status = measurement_impedance_status,
        has_append_measurement_data = has_append_measurement_data)

class TrisaBodyAnalyzeSmartScale(gatt.Device):
    def __init__(self, mac_address, manager, managed=True):
        super().__init__(mac_address, manager, managed)
        self.download_command_characteristic = None
        self.measurement_characteristic_notifications_enabled = False
        self.append_measurement_characteristic_notifications_enabled = False
        self.upload_command_characteristic_notifications_enabled = False
        self.authenticating = False
        self.authenticated = False

    def services_resolved(self):
        super().services_resolved()

        print('Device name:', self.alias())

        all_characteristics = {}
        for s in self.services:
            for c in s.characteristics:
                all_characteristics[s.uuid, c.uuid] = c

        measurement_characteristic = all_characteristics[WEIGHT_SCALE_SERVICE_UUID, MEASUREMENT_CHARACTERISTIC_UUID]
        append_measurement_characteristic = all_characteristics[WEIGHT_SCALE_SERVICE_UUID, APPEND_MEASUREMENT_CHARACTERISTIC_UUID]
        self.download_command_characteristic = all_characteristics[WEIGHT_SCALE_SERVICE_UUID, DOWNLOAD_COMMAND_CHARACTERISTIC_UUID]
        upload_command_characteristic = all_characteristics[WEIGHT_SCALE_SERVICE_UUID, UPLOAD_COMMAND_CHARACTERISTIC_UUID]

        measurement_characteristic.enable_notifications()
        append_measurement_characteristic.enable_notifications()
        upload_command_characteristic.enable_notifications()

    def set_notifications_enabled(self, characteristic, value):
        if characteristic.uuid == MEASUREMENT_CHARACTERISTIC_UUID:
            self.measurement_characteristic_notifications_enabled = value
        elif characteristic.uuid == APPEND_MEASUREMENT_CHARACTERISTIC_UUID:
            self.append_measurement_characteristic_notifications_enabled = value
        elif characteristic.uuid == UPLOAD_COMMAND_CHARACTERISTIC_UUID:
            self.upload_command_characteristic_notifications_enabled = value

    def on_notifications_enabled(self):
        print('All notifications enabled.')

    def all_notifications_enabled(self):
        return (
            self.measurement_characteristic_notifications_enabled and
            self.append_measurement_characteristic_notifications_enabled and
            self.upload_command_characteristic_notifications_enabled)

    def send(self, command):
        print('Sending', command.hex())
        self.download_command_characteristic.write_value(command)

    def characteristic_value_updated(self, characteristic, value):
        if characteristic.uuid == UPLOAD_COMMAND_CHARACTERISTIC_UUID:
            if len(value) > 0 and value[0] == 0xa0:
                assert len(value) >= 5
                global password
                password = value[1:5]
                print('Received password:', password.hex())
                SavePassword()
                self.send(GetSetBroadcastIdCommand())
                return
            if len(value) > 0 and value[0] == 0xa1:
                assert len(value) >= 5
                challenge = value[1:5]
                print('Received challenge', challenge.hex())
                if not password:
                    print('Cannot reply because password is not set! ' +
                          'Switch the scale to pairing mode to retrive its password.')
                elif self.authenticated:
                    print('Already authenticated?!')
                else:
                    self.authenticating = True
                    self.send(GetAuthCommand(challenge))
                return
        if characteristic.uuid == MEASUREMENT_CHARACTERISTIC_UUID:
            print('Received weight data', value.hex())
            print(ParseWeightScaleMeasurementData(value))
            return

        print('Unregognized characteristic value:', characteristic.uuid, value.hex())

    def characteristic_write_value_succeeded(self, characteristic):
        super().characteristic_write_value_succeeded(characteristic)
        if self.authenticating:
            self.authenticating = False
            self.authenticated = True
            self.send(GetUtcCommand())

    def characteristic_write_value_failed(self, characteristic, error):
        self.set_notifications_enabled(characteristic, False)
        super().characteristic_write_value_failed(characteristic, error)
        print('Characteristic write value failed', characteristic.uuid, error)

    def characteristic_enable_notifications_succeeded(self, characteristic):
        super().characteristic_enable_notifications_succeeded(characteristic)
        print('Characteristic enable notifications succeeded', characteristic.uuid)
        enabled_before = self.all_notifications_enabled()
        self.set_notifications_enabled(characteristic, True)
        enabled_after = self.all_notifications_enabled()
        if enabled_after and not enabled_before:
            self.on_notifications_enabled()

    def characteristic_enable_notifications_failed(self, characteristic, error):
        super().characteristic_enable_notifications_failed(characteristic, error)
        print('Characteristic enable notifications failed', characteristic.uuid, error)

def Main():
    # The scale broadcasts a password when it is put in pairing mode.
    # This password is necessary to connect to it later (without having to re-pair).
    global password
    password = LoadPassword()
    if not password:
        print('Could not load password! Put the scale in pairing mode to retrieve it.')
        print('Hit ^C to disconnect and finish pairing.')
    manager = gatt.DeviceManager(adapter_name=ADAPTER)
    print('Connecting to MAC', MAC)
    device = TrisaBodyAnalyzeSmartScale(manager=manager, mac_address=MAC)
    device.connect()
    try:
        manager.run()
    except KeyboardInterrupt:
        print('Interrupted!')
        device.send(GetDisconnectCommand())
        device.disconnect()
        manager.run()

Main()

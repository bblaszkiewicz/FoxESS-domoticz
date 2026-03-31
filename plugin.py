"""
<plugin key="foxess" name="FoxESS Inverter Plugin" version="0.2.0" author="BBlaszkiewicz">
    <params>
        <param field="Mode1" label="Inverter Serial Number" width="200px" required="true" default=""/>
        <param field="Mode2" label="API Key" width="300px" required="true" default=""/>
        <param field="Mode3" label="Check every x minutes" width="40px" default="5" required="true" />
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="False" value="false" default="true" />
                <option label="True" value="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import json
import time
import hashlib
import requests
import datetime


VARIABLE_MAP = [
    # zmienne wspólne (ongrid + hybrid)
    ('pvPower',              1, "PV Power",           "Usage",       False),
    ('ambientTemperation',   2, "Ambient Temp",        "Temperature", False),
    ('invTemperation',       3, "Inv Temperature",     "Temperature", False),
    ('generation',           4, "Energy",              "kWh",         False),
    # zmienne tylko dla hybrydowych (bateria)
    ('batVolt',              5, "Battery Voltage",     None,          True),   # Type=243, Subtype=8
    ('generationPower',      6, "Generation Power",    "Usage",       True),
    ('gridConsumptionPower', 7, "Grid Consumption",    "Usage",       True),
    ('loadsPower',           8, "Loads Power",         "Usage",       True),
    ('meterPower',           9, "Meter Power",         "Usage",       True),
]

ALL_VARIABLES = [entry[0] for entry in VARIABLE_MAP]


class BasePlugin:
    enabled = False

    def __init__(self):
        self.inverter_sn = None
        self.api_key = None
        self.api_url = 'https://www.foxesscloud.com'
        self.devices_created = False
        self.has_battery = False          
        self.battery_detected = False     
        self.pollinterval = 300
        self.nextpoll = datetime.datetime.now()

    def onStart(self):
        Domoticz.Log("FoxESS Plugin Started")

        self.inverter_sn = Parameters["Mode1"]
        self.api_key = Parameters["Mode2"]
        self.pollinterval = int(Parameters["Mode3"]) * 60

        if not self.inverter_sn or not self.api_key:
            Domoticz.Error("FoxESS: Brak numeru seryjnego lub klucza API w konfiguracji.")
            return

        self._detect_inverter_type()

        self._create_devices()

    def onStop(self):
        Domoticz.Log("FoxESS Plugin Stopped")

    def onHeartbeat(self):
        if not self.devices_created:
            self.onStart()

        now = datetime.datetime.now()
        if now < self.nextpoll:
            Domoticz.Debug(("Awaiting next poll: %s") % str(self.nextpoll))
            return

        self.postponeNextPool(seconds=self.pollinterval)

        try:
            self.get_real_time_data()
        except Exception as e:
            Domoticz.Log(f"heartbeat fail: {e}")

    def _detect_inverter_type(self):
        path = '/op/v0/device/detail'
        data = self.api_request('get', path, params={'sn': self.inverter_sn})

        if data and 'result' in data:
            self.has_battery = bool(data['result'].get('hasBattery', False))
            self.battery_detected = True
            device_type = data['result'].get('deviceType', 'unknown')
            Domoticz.Log(
                f"FoxESS: deviceType={device_type}, "
                f"hasBattery={self.has_battery}"
            )
        else:
            Domoticz.Error(
                "FoxESS: Nie udało się pobrać informacji o urządzeniu. "
                "Zakładam inwerter ongrid (bez baterii)."
            )
            self.has_battery = False
            self.battery_detected = True

    def _create_devices(self):
        for (var_name, unit_id, dev_name, type_name, hybrid_only) in VARIABLE_MAP:
            if hybrid_only and not self.has_battery:
                continue

            if unit_id not in Devices:
                if type_name is None:
                    Domoticz.Device(Name=dev_name, Unit=unit_id, Type=243, Subtype=8).Create()
                else:
                    Domoticz.Device(Name=dev_name, Unit=unit_id, TypeName=type_name).Create()
                Domoticz.Log(f"FoxESS: Utworzono urządzenie Unit={unit_id} '{dev_name}'")

        self.devices_created = True

    
    def get_real_time_data(self):
        try:
            path = '/op/v0/device/real/query'
            requested_vars = [
                var for (var, unit_id, _, _, hybrid_only) in VARIABLE_MAP
                if not (hybrid_only and not self.has_battery)
            ]
            params = {'sn': self.inverter_sn, 'variables': requested_vars}
            data = self.api_request('post', path, params)

            if not (data and 'result' in data):
                Domoticz.Log("FoxESS: Brak danych real-time w odpowiedzi API")
                return None

            datas = data['result'][0].get('datas', [])
            values = {item['variable']: item.get('value', 0) for item in datas}

            Domoticz.Log(f"FoxESS real-time values: {values}")

            for (var_name, unit_id, dev_name, type_name, hybrid_only) in VARIABLE_MAP:
                if hybrid_only and not self.has_battery:
                    continue
                if unit_id not in Devices:
                    continue

                value = values.get(var_name, 0) or 0

                if type_name == "kWh":
                    pv_power = values.get('pvPower', 0) or 0
                    s_value = f"{pv_power * 1000};{value * 1000}"
                    Devices[unit_id].Update(0, s_value)
                elif type_name == "Temperature":
                    Devices[unit_id].Update(nValue=0, sValue=str(value))
                elif type_name is None:
                    Devices[unit_id].Update(nValue=0, sValue=str(value))
                else:
                    Devices[unit_id].Update(nValue=0, sValue=str(value * 1000))

        except Exception as e:
            Domoticz.Log(f"get_real_time_data fail: {e}")

        return None

    def get_total_energy(self):
        try:
            path = '/op/v0/device/generation'
            params = {'sn': self.inverter_sn}
            data = self.api_request('get', path, params)

            if data and 'result' in data:
                return data['result'].get('cumulative', 0)
        except Exception as e:
            Domoticz.Log(f"get_total_energy fail: {e}")
        return None

    def report_query(self):
        path = '/op/v0/device/report/query'
        request_param = {
            "sn": self.inverter_sn,
            "year": 2024, "month": 9, 'day': 23, "dimension": "day",
            "variables": ["generation", "feedin", "gridConsumption",
                          "chargeEnergyTotal", "dischargeEnergyTotal"]
        }
        response = self.api_request('post', path, request_param)
        if response and 'data' in response:
            Domoticz.Log(f"Report data: {json.dumps(response['data'])}")
        else:
            Domoticz.Error("Failed to retrieve report data")

    def get_signature(self, path):
        timestamp = round(time.time() * 1000)
        signature_string = fr"{path}\r\n{self.api_key}\r\n{timestamp}"
        signature = hashlib.md5(signature_string.encode('utf-8')).hexdigest()

        return {
            'Content-Type': 'application/json',
            'token': self.api_key,
            'signature': signature,
            'timestamp': str(timestamp),
            'lang': 'en',
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/117.0.0.0 Safari/537.36'
            )
        }

    def api_request(self, method, path, params=None):
        headers = self.get_signature(path)
        url = f"{self.api_url}{path}"

        try:
            if method == 'get':
                response = requests.get(url, params=params, headers=headers, verify=False)
            elif method == 'post':
                response = requests.post(url, json=params, headers=headers, verify=False)
            response.raise_for_status()
            Domoticz.Log(response.json())
            return response.json()
        except Exception as e:
            Domoticz.Error(f"Error communicating with FoxESS API: {str(e)}")
            return None

    def postponeNextPool(self, seconds=3600):
        self.nextpoll = (datetime.datetime.now() + datetime.timedelta(seconds=seconds))
        return self.nextpoll


def onStart():
    global _plugin
    _plugin = BasePlugin()
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

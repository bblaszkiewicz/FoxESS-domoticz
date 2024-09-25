"""
<plugin key="foxess" name="FoxESS Inverter Plugin" version="0.1.1" author="BBlaszkiewicz">
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

class BasePlugin:
    enabled = False

    def __init__(self):
        self.inverter_sn = None
        self.api_key = None
        self.api_url = 'https://www.foxesscloud.com'
        self.devices_created = False
        self.pollinterval = 300
        self.nextpoll = datetime.datetime.now()

    def onStart(self):
        Domoticz.Log("FoxESS Plugin Started")

        # Pobierz wartości wprowadzone w panelu konfiguracyjnym Domoticz
        self.inverter_sn = Parameters["Mode1"]  # Numer seryjny inwertera
        self.api_key = Parameters["Mode2"]  # API key
        self.pollinterval = int(Parameters["Mode3"]) * 60

        if not self.inverter_sn or not self.api_key:
            Domoticz.Error("FoxESS: Brak numeru seryjnego lub klucza API w konfiguracji.")
            return

        # Tworzenie urządzeń
        if 1 not in Devices:
            Domoticz.Device(Name="Energy", Unit=1, TypeName="kWh").Create()
        self.devices_created = True

    def onStop(self):
        Domoticz.Log("FoxESS Plugin Stopped")

    def onHeartbeat(self):
        if not self.devices_created:
            self.onStart()
            
        now = datetime.datetime.now()
        if now < self.nextpoll:
            Domoticz.Debug(("Awaiting next pool: %s") % str(self.nextpoll))
            return
            
        
        # Set next pool time
        self.postponeNextPool(seconds=self.pollinterval)
        
        try:
            current_power = self.get_real_time_data()
            total_energy = self.get_total_energy()
            Domoticz.Log(f"power: {current_power}")
            Domoticz.Log(f"total energy: {total_energy}")

            # Aktualizacja urządzeń Domoticz
            if total_energy is not None and current_power is not None:
                Devices[1].Update(0, f"{str(current_power*1000)};{str(total_energy*1000)}")
        except:
            Domoticz.Log("heartbeat fail")

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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36' 
        }

    def api_request(self, method, path, params=None):
        headers = self.get_signature(path)
        url = f"{self.api_url}{path}"

        try:
            if method == 'get':
                response = requests.get(url, params=params, headers=headers, verify=False)
            elif method == 'post':
                response = requests.post(url, json=params, headers=headers, verify=False)
            response.raise_for_status()  # Zgłoś wyjątek w przypadku błędu HTTP
            Domoticz.Log(response.json())
            return response.json() 
        except Exception as e:
            Domoticz.Error(f"Error communicating with FoxESS API: {str(e)}")
            return None

    def get_real_time_data(self):
        try:
            path = '/op/v0/device/real/query'
            params = {'sn': self.inverter_sn, 'variables': ['pvPower']}
            data = self.api_request('post', path, params)

            if data and 'result' in data:
                #Domoticz.Log(f"Real-time data: {json.dumps(data)}")  # Logowanie danych
                return data['result'][0].get('datas',0)[0].get('value',0)
        except:
            Domoticz.Log("get_real_time_data fail")
        return None

    def get_total_energy(self):
        try:
            path = '/op/v0/device/generation'
            params = {'sn': self.inverter_sn}
            data = self.api_request('get', path, params)

            if data and 'result' in data:
                #Domoticz.Log(f"Total energy data: {json.dumps(data)}")  # Logowanie danych
                return data['result'].get('cumulative', 0) 
        except:
            Domoticz.Log("get_total_energy fail")
        return None

    def report_query(self):
        path = '/op/v0/device/report/query'
        request_param = {
            "sn": self.inverter_sn,
            "year": 2024, "month": 9, 'day': 23, "dimension": "day",
            "variables": ["generation", "feedin", "gridConsumption", "chargeEnergyTotal", "dischargeEnergyTotal"]
        }
        response = self.api_request('post', path, request_param)
        if response and 'data' in response:
            Domoticz.Log(f"Report data: {json.dumps(response['data'])}")
        else:
            Domoticz.Error("Failed to retrieve report data")
    
    def postponeNextPool(self, seconds=3600):
        self.nextpoll = (datetime.datetime.now() + datetime.timedelta(seconds=seconds))
        return self.nextpoll

# Funkcje wymagane przez Domoticz
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



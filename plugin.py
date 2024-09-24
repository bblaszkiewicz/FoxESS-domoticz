"""
<plugin key="foxess" name="FoxESS Inverter Plugin" version="0.1.0" author="BBlaszkiewicz">
    <params>
        <param field="Mode1" label="Inverter Serial Number" width="200px" required="true" default=""/>
        <param field="Mode2" label="API Key" width="300px" required="true" default=""/>
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

class BasePlugin:
    enabled = False

    def __init__(self):
        self.inverter_sn = None
        self.api_key = None
        self.api_url = 'https://www.foxesscloud.com'
        self.devices_created = False

    def onStart(self):
        Domoticz.Log("FoxESS Plugin Started")

        # Pobierz wartości wprowadzone w panelu konfiguracyjnym Domoticz
        self.inverter_sn = Parameters["Mode1"]  # Numer seryjny inwertera
        self.api_key = Parameters["Mode2"]  # API key

        if not self.inverter_sn or not self.api_key:
            Domoticz.Error("FoxESS: Brak numeru seryjnego lub klucza API w konfiguracji.")
            return

        # Tworzenie urządzeń w Domoticz dla bieżącej mocy i całkowitej energii
        if 1 not in Devices:
            Domoticz.Device(Name="Current Power", Unit=1, TypeName="Usage").Create()
        if 2 not in Devices:
            Domoticz.Device(Name="Total Energy", Unit=2, TypeName="kWh").Create()
        self.devices_created = True

    def onStop(self):
        Domoticz.Log("FoxESS Plugin Stopped")

    def onHeartbeat(self):
        if not self.devices_created:
            self.onStart()

        # Pobierz aktualną moc i całkowitą energię z API FoxESS
        current_power = self.get_real_time_data()
        total_energy = self.get_total_energy()
        Domoticz.Log(total_energy)

        # Aktualizacja urządzeń Domoticz
        if current_power is not None:
            Devices[1].Update(0, str(current_power))
        if total_energy is not None:
            Devices[2].Update(0, str(total_energy))

    def get_signature(self, path):
        # Generowanie sygnatury zgodnie z wymogami API FoxESS
        timestamp = round(time.time() * 1000)
        signature_string = fr"{path}\r\n{self.api_key}\r\n{timestamp}"
        signature = hashlib.md5(signature_string.encode('utf-8')).hexdigest()

        # Zwracamy nagłówki z wymaganymi parametrami
        return {
            'Content-Type': 'application/json',  # JSON jest wymagany przez API FoxESS
            'token': self.api_key,
            'signature': signature,
            'timestamp': str(timestamp),
            'lang': 'en',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'  # Przykładowy User-Agent
        }

    def api_request(self, method, path, params=None):
        headers = self.get_signature(path)  # Pobierz poprawne nagłówki
        url = f"{self.api_url}{path}"

        try:
            if method == 'get':
                response = requests.get(url, params=params, headers=headers, verify=False)
            elif method == 'post':
                response = requests.post(url, json=params, headers=headers, verify=False)
            response.raise_for_status()  # Zgłoś wyjątek w przypadku błędu HTTP
            Domoticz.Log(response.json())
            return response.json()  # Zwróć odpowiedź JSON
        except Exception as e:
            Domoticz.Error(f"Error communicating with FoxESS API: {str(e)}")
            return None

    def get_real_time_data(self):
        path = '/op/v0/device/real/query'
        params = {'sn': self.inverter_sn, 'variables': ['pvPower']}
        data = self.api_request('post', path, params)

        if data and 'result' in data:
            Domoticz.Log(f"Real-time data: {json.dumps(data)}")  # Logowanie danych
            Domoticz.Log(data['result'][0].get('datas',0)[0].get('value',0))
            return data['result'][0].get('value', 0)  # Zwróć bieżącą moc
        return None

    def get_total_energy(self):
        path = '/op/v0/device/generation'
        params = {'sn': self.inverter_sn}
        data = self.api_request('get', path, params)  # Zmiana na GET dla poprawności API

        if data and 'result' in data:
            Domoticz.Log(f"Total energy data: {json.dumps(data)}")  # Logowanie danych
            return data['result'].get('cumulative', 0)  # Pobierz wartość 'total_energy'
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
            Domoticz.Log(f"Report data: {json.dumps(response['data'])}")  # Logowanie raportu
        else:
            Domoticz.Error("Failed to retrieve report data")

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



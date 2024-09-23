import json
import time
import urllib3
import requests
import hashlib
import os
from json import JSONDecodeError
"""debug mode"""


debug = False


"""request interval (second)"""


sleep_time = 0


"""domain name, do not modify it unless necessary"""


domain = 'https://www.foxesscloud.com'


"""your key"""


key = ''


class GetAuth:


def get_signature(self, token, path, lang='en'):


"""


This function is used to generate a signature consisting of URL, token, and timestamp, and return a dictionary containing the signature and other information.


:param token: your key


:param path:  your request path


:param lang: language, default is English.


:return: with authentication header


"""


timestamp = round(time.time() * 1000)


signature = fr'{path}\r\n{token}\r\n{timestamp}'


result = {


'token': token,


'lang': lang,


'timestamp': str(timestamp),


'signature': self.md5c(text=signature),


'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '


'Chrome/117.0.0.0 Safari/537.36'


}


return result


@staticmethod


def md5c(text="", _type="lower"):


res = hashlib.md5(text.encode(encoding='UTF-8')).hexdigest()


if _type.eq("lower"):


return res


else:


return res.upper()


def save_response_data(response, filename):


"""Create the 'data' directory if it doesn't exist"""


os.makedirs('data', exist_ok=True)


"""Concatenate the directory path and filename to create the full file path"""


file_path = os.path.join('data', filename)


"""Get the current timestamp"""


timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


"""Check if the status code is 200"""


if response.status_code == 200:


"""Save the response data and timestamp to a dictionary"""


try:


response_json = response.json()


except JSONDecodeError:


response_json = response.text


data = {


'response': response_json,


'timestamp': timestamp


}


"""Write the dictionary as JSON to the file"""


with open(file_path, 'w', encoding='utf-8') as file:


json.dump(data, file, ensure_ascii=False, indent=4)


else:


"""Save the status code, response text, and timestamp to a dictionary"""


data = {


'status_code': response.status_code,


'response_text': response.text,


'timestamp': timestamp


}


"""Write the dictionary as JSON to the file"""


with open(file_path, 'w', encoding='utf-8') as file:


json.dump(data, file, ensure_ascii=False, indent=4)


print(f'{timestamp}: [{filename}] successfully saved')


urllib3.disable_warnings()


def fr_requests(method, path, param=None):


url = domain + path


headers = GetAuth().get_signature(token=key, path=path)


time.sleep(sleep_time)


if method == 'get':


response = requests.get(url=url, params=param, headers=headers, verify=False)


elif method == 'post':


response = requests.post(url=url, json=param, headers=headers, verify=False)


else:


raise Exception('request method error')


if debug:


result = {'url': url, 'method': method, 'param': param, 'headers': headers, 'response': response.text}


print(json.dumps(result, indent=1))


print('-------------------------' * 5)


return response


class Plant:


@staticmethod


def plant_list():


path = '/op/v0/plant/list'


request_param = {'currentPage': 1, 'pageSize': 10}


response = fr_requests('post', path, request_param)


save_response_data(response, 'plant_list_response.json')


return response


@staticmethod


def plant_detail():


path = '/op/v0/plant/detail'


request_param = {'id': 'abc'}


response = fr_requests('get', path, request_param)


save_response_data(response, 'plant_detail_response.json')


return response


class Device:


@staticmethod


def device_list():


path = '/op/v0/device/list'


request_param = {'currentPage': 1, 'pageSize': 500}


response = fr_requests('post', path, request_param)


save_response_data(response, 'device_list_response.json')


return response


@staticmethod


def device_detail():


path = '/op/v0/device/detail'


request_param = {'sn': 'sn'}


response = fr_requests('get', path, request_param)


save_response_data(response, 'device_detail_response.json')


return response


@staticmethod


def variable_get():


path = '/op/v0/device/variable/get'


response = fr_requests('get', path)


save_response_data(response, 'device_variable_get_response.json')


return response


@staticmethod


def real_query():


path = '/op/v0/device/real/query'


request_param = {'sn': 'sn', 'variables': []}


response = fr_requests('post', path, request_param)


save_response_data(response, 'device_real_query_response.json')


return response


@staticmethod


def history_query():


path = '/op/v0/device/history/query'


"""get the current millisecond level timestamp"""


end_time = int(time.time() * 1000)


"""timestamp 24 hours ago"""


begin_time = end_time - 3600000


request_param = {'sn': 'sn', 'variables': [], 'begin': begin_time, 'end': end_time}


response = fr_requests('post', path, request_param)


save_response_data(response, 'device_history_query_response.json')


return response


@staticmethod


def report_query():


path = '/op/v0/device/report/query'


request_param = {"sn": "sn",


"year": 2024, "month": 1, 'day': 17, "dimension": "day",


"variables": ["generation", "feedin", "gridConsumption",


"chargeEnergyToTal", "dischargeEnergyToTal"]}


response = fr_requests('post', path, request_param)


save_response_data(response, 'device_report_query_response.json')


return response


@staticmethod


def device_generation():


path = '/op/v0/device/generation'


request_param = {'sn': 'sn'}


response = fr_requests('get', path, request_param)


save_response_data(response, 'device_generation_response.json')


return response


@staticmethod


def device_bat_soc_get():


path = '/op/v0/device/battery/soc/get'


request_param = {'sn': 'sn'}


response = fr_requests('get', path, request_param)


save_response_data(response, 'device_bat_soc_get_response.json')


return response


@staticmethod


def device_bat_soc_set():


path = '/op/v0/device/battery/soc/set'


request_param = {'sn': 'sn', 'minSoc': 10, 'minSocOnGrid': 10}


response = fr_requests('post', path, request_param)


save_response_data(response, 'device_bat_soc_set_response.json')


return response


@staticmethod


def device_bat_force_charge_time_get():


path = '/op/v0/device/battery/forceChargeTime/get'


request_param = {'sn': 'sn'}


response = fr_requests('get', path, request_param)


save_response_data(response, 'device_bat_force_charge_time_get_response.json')


return response


@staticmethod


def device_bat_force_charge_time_set():


path = '/op/v0/device/battery/forceChargeTime/set'


request_param = {"sn": "sn", "enable1": True, "enable2": False,


"startTime1": {"hour": 12, "minute": 0}, "endTime1": {"hour": 14, "minute": 56},


"startTime2": {"hour": 2, "minute": 0}, "endTime2": {"hour": 4, "minute": 0}}


"""


request_param = {"sn": "sn", "enable1": False, "enable2": False,


"startTime1": {"hour": 11, "minute": 1}, "endTime1": {"hour": 15, "minute": 57},


"startTime2": {"hour": 3, "minute": 1}, "endTime2": {"hour": 5, "minute": 1}}


"""


response = fr_requests('post', path, request_param)


save_response_data(response, 'device_bat_force_charge_time_set_response.json')


return response


@staticmethod


def device_scheduler_get_flag():


path = '/op/v0/device/scheduler/get/flag'


request_param = {'deviceSN': 'sn'}


response = fr_requests('post', path, request_param)


save_response_data(response, 'device_scheduler_get_flag_response.json')


return response


@staticmethod


def device_scheduler_set_flag():


path = '/op/v0/device/scheduler/set'


request_param = {'deviceSN': 'sn', 'enable': 0}


response = fr_requests('post', path, request_param)


save_response_data(response, 'device_scheduler_set_flag_response.json')


return response


@staticmethod


def device_scheduler_get():


path = '/op/v0/device/scheduler/get'


request_param = {'deviceSN': 'sn'}


response = fr_requests('post', path, request_param)


save_response_data(response, 'device_scheduler_get_response.json')


return response


@staticmethod


def device_scheduler_enable():


path = '/op/v0/device/scheduler/enable'


request_param1 = {"deviceSN": "sn",


"groups": [{"enable": 1, "startHour": 0, "startMinute": 0, "endHour": 1, "endMinute": 59,


"workMode": "SelfUse", "minSocOnGrid": 11, "fdSoc": 12, "fdPwr": 5001},


{"enable": 1, "startHour": 2, "startMinute": 1, "endHour": 3, "endMinute": 0,


"workMode": "SelfUse", "minSocOnGrid": 21, "fdSoc": 22, "fdPwr": 5002},


{"enable": 1, "startHour": 3, "startMinute": 1, "endHour": 3, "endMinute": 58,


"workMode": "Feedin", "minSocOnGrid": 31, "fdSoc": 32, "fdPwr": 5003},


{"enable": 1, "startHour": 4, "startMinute": 1, "endHour": 4, "endMinute": 58,


"workMode": "Backup", "minSocOnGrid": 41, "fdSoc": 42, "fdPwr": 5004},


{"enable": 1, "startHour": 5, "startMinute": 1, "endHour": 5, "endMinute": 58,


"workMode": "ForceCharge", "minSocOnGrid": 51, "fdSoc": 52, "fdPwr": 5005},


{"enable": 1, "startHour": 6, "startMinute": 1, "endHour": 6, "endMinute": 58,


"workMode": "ForceDischarge", "minSocOnGrid": 61, "fdSoc": 62, "fdPwr": 5006},


{"enable": 1, "startHour": 7, "startMinute": 0, "endHour": 7, "endMinute": 59,


"workMode": "ForceDischarge", "minSocOnGrid": 71, "fdSoc": 72, "fdPwr": 0},


{"enable": 1, "startHour": 8, "startMinute": 0, "endHour": 23, "endMinute": 59,


"workMode": "ForceDischarge", "minSocOnGrid": 81, "fdSoc": 82, "fdPwr": 6000}]}


request_param2 = {"deviceSN": "sn",


"groups": [{"enable": 0, "startHour": 0, "startMinute": 0, "endHour": 0, "endMinute": 1,


"workMode": "ForceCharge", "minSocOnGrid": 10, "fdSoc": 0, "fdPwr": 0},


{"enable": 0, "startHour": 3, "startMinute": 2, "endHour": 4, "endMinute": 1,


"workMode": "ForceCharge", "minSocOnGrid": 22, "fdSoc": 23, "fdPwr": 5003},


{"enable": 0, "startHour": 4, "startMinute": 2, "endHour": 4, "endMinute": 59,


"workMode": "Backup", "minSocOnGrid": 32, "fdSoc": 32, "fdPwr": 5004},


{"enable": 0, "startHour": 5, "startMinute": 2, "endHour": 5, "endMinute": 59,


"workMode": "Feedin", "minSocOnGrid": 42, "fdSoc": 42, "fdPwr": 5005},


{"enable": 0, "startHour": 6, "startMinute": 2, "endHour": 6, "endMinute": 59,


"workMode": "SelfUse", "minSocOnGrid": 52, "fdSoc": 52, "fdPwr": 5006},


{"enable": 0, "startHour": 7, "startMinute": 1, "endHour": 7, "endMinute": 59,


"workMode": "SelfUse", "minSocOnGrid": 62, "fdSoc": 62, "fdPwr": 5007},


{"enable": 0, "startHour": 8, "startMinute": 1, "endHour": 8, "endMinute": 3,


"workMode": "SelfUse", "minSocOnGrid": 72, "fdSoc": 72, "fdPwr": 0},


{"enable": 0, "startHour": 22, "startMinute": 59, "endHour": 23, "endMinute": 59,


"workMode": "SelfUse", "minSocOnGrid": 100, "fdSoc": 100, "fdPwr": 6000}]}


response = fr_requests('post', path, request_param2)


save_response_data(response, 'device_scheduler_set_response.json')


return response


class Module:


@staticmethod


def module_list():


path = '/op/v0/module/list'


request_param = {'currentPage': 1, 'pageSize': 10}


response = fr_requests('post', path, request_param)


save_response_data(response, 'module_list_response.json')


return response


class User:


@staticmethod


def user_get_access_count():


path = '/op/v0/user/getAccessCount'


response = fr_requests('get', path)


save_response_data(response, 'user_get_access_count_response.json')


return response


if name == 'main':


plant = Plant()


"""


plant.plant_list()


plant.plant_detail()


"""


device = Device()


"""


device.device_list()


device.device_detail()


device.variable_get()


device.real_query()


device.history_query()


device.report_query()


device.device_generation()


device.device_bat_soc_set()


time.sleep(3)


device.device_bat_soc_get()


device.device_bat_force_charge_time_set()


time.sleep(3)


device.device_bat_force_charge_time_get()


device.device_scheduler_set_flag()


time.sleep(3)


device.device_scheduler_get_flag()


device.device_scheduler_enable()


time.sleep(3)


device.device_scheduler_get()


"""


module = Module()


"""


module.module_list()


"""


user = User()


"""


user.user_get_access_count()


"""

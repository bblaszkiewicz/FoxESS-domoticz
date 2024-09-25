# FoxESS & Domoticz integration
![FOX-logo-425-218-4 (1)](https://github.com/user-attachments/assets/267b9b13-134d-481e-a818-46442d89a967) ![domoticz_logotyp_mini-330x220](https://github.com/user-attachments/assets/6140e90a-1314-438c-84c9-5bc1fdcc595b)</br>
Plugin for reading data from the FoxESS inverter. Currently, it allows reading the current power and total production. The plugin will be further developed to allow reading more data.
## Instalation
Navigate to the plugin directory and install the plugin straight from github
```
cd domoticz/plugins
git clone https://github.com/bblaszkiewicz/FoxESS-domoticz.git FoxESS
```
Next, restart Domoticz sa that it will find the plugin
```
sudo systemctl restart domoticz.service
```
## Configuration
Enter your inverter's API key and serial number</br>
![image](https://github.com/user-attachments/assets/b97e9e68-2d95-4188-8530-896bcb596df4)
### How to find API key
After logging in to https://www.foxesscloud.com/ click the user icon located in the upper right corner of the window. Then click _User Profile_ and go to the _API Management_ tab. Click _Generate API key_. The key will appear in the field next to it.</br>
![image](https://github.com/user-attachments/assets/88d250a5-60e1-47dc-b049-1452fccb9826)


# BadBlue (Windows)


CVE-2024-21306 BadBlue implementation (Using DuckyScript)

Unauthenticated Peering Leading to Code Execution (Using HID Keyboard)

[This is an implementation of the CVE discovered by marcnewlin](https://github.com/marcnewlin/hi_my_name_is_keyboard)

[And BlueDucky](https://github.com/pentestfunctions/BlueDucky)

## Introduction
BabBlue is a powerful tool for exploiting a vulnerability in Bluetooth devices. By running this script, you can:

1. Load saved Bluetooth devices that are no longer visible but have Bluetooth still enabled.
2. Automatically save any devices you scan.
3. Send payload via ducky script format to interact with devices.

I've successfully run this on any Raspberry Pi 4 and VirtualBox using the CRS 4.0, ORICO 4.0,.. Bluetooth module. It works against various Windows with version lower .3007 .

## Installation and Usage

### Setup Instructions

```bash
# update apt
sudo apt-get update
sudo apt-get -y upgrade

# install dependencies from apt
sudo apt install -y bluez-tools bluez-hcidump libbluetooth-dev \
                    git gcc python3-pip python3-setuptools \
                    python3-pydbus dbus-x11

# install pybluez from source
git clone https://github.com/pybluez/pybluez.git
cd pybluez
sudo python3 setup.py install

# build bdaddr from the bluez source
cd ~/
git clone --depth=1 https://github.com/bluez/bluez.git
gcc -o bdaddr ~/bluez/tools/bdaddr.c ~/bluez/src/oui.c -I ~/bluez -lbluetooth
sudo cp bdaddr /usr/local/bin/
```

## Running BabBlue
```bash
git clone https://github.com/PhucHauDeveloper/BabBlue.git
cd BabBlue
sudo hciconfig hci0 up
python3 BabBlue.py
```
-k is Keyboard(default my keyboard F4:73:35:7A:4B:BB, you need change it)

-i is interface(default hci0)

-c is target windows devices(type blank tool auto scan for you)

## Operational Steps
1. On running, it prompts for the target MAC address.
2. Pressing nothing triggers an automatic scan for devices.
3. Devices previously found are stored in known_devices.txt.
4. If known_devices.txt exists, it checks this file before scanning.
5. Executes using payload.txt file.
6. Successful execution will result in automatic connection and script running.

## Duckyscript
Work in Progress:
- Suggest me ideas

## Know Bug
'/' char can't send


#### Example payload.txt:
```bash
REM Title of the payload
STRING ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*()_-=+\|[{]};:'",<.>/?
GUI D
```

```bash
REM Opens RickRoll
DELAY 200
GUI r
DELAY 200
STRING https://www.youtube.com/watch?v=dQw4w9WgXcQ
DELAY 300
ENTER
DELAY 300
```

## Enjoy experimenting with BabBlue!








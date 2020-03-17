from time import sleep
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

# from adafruit_ble.uart_client import UARTClient
# from adafruit_ble.scanner import Scanner
# from adafruit_bluefruit_connect.packet import Packet
from adafruit_bluefruit_connect.button_packet import ButtonPacket
from adafruit_bluefruit_connect.color_packet import ColorPacket

from neopixel import NeoPixel
from board import NEOPIXEL, SWITCH
from adafruit_debouncer import Debouncer
from digitalio import DigitalInOut, Direction, Pull
import adafruit_fancyled.adafruit_fancyled as fancy

pin = DigitalInOut(SWITCH)  # Set up built-in pushbutton switch
pin.direction = Direction.INPUT
pin.pull = Pull.UP
switch = Debouncer(pin)

pixels = NeoPixel(NEOPIXEL, 1)  # Set up built-in NeoPixel

AQUA = 0x00FFFF    # (0, 255, 255)
GREEN = 0x00FF00   # (0, 255, 0)
ORANGE = 0xFF8000  # (255, 128, 0)
RED = 0xFF0000     # (255, 0, 0)
BLUE = 0x0000FF    # (0, 0, 255)

gradients = {'Off': [(0.0, RED), (0.75, ORANGE)],
             'On':  [(0.0, GREEN), (1.0, AQUA)]}
palette = fancy.expand_gradient(gradients['Off'], 30)

gamma_levels = (0.25, 0.3, 0.15)
color_index = 1
fade_direction = 1

ble = BLERadio()
TARGET = 'FD:F8:DE:77:DE:55'  # CHANGE TO YOUR BLE ADDRESS

button_packet = ButtonPacket("1", True)  # Transmits pressed button 1

# scanner = Scanner()  # BLE Scanner
# uart_client = UARTClient()  # BLE Client

uart_connection = None
# See if any existing connections are providing UARTService.
def bytes_to_ble_addr(byte_arr):
    b = list(byte_arr)
    if len(b) == 6:
        hex_6 = ''.join('{:02X}:'.format(a) for a in reversed(b))[:-1]
    else:
        hex_6 = ''
    return hex_6

print('is BLE connected')
if ble.connected:
    for connection in ble.connections:
        if UARTService in connection:
            uart_connection = connection
        break

while True:
    if not uart_connection:
        print("Scanning...")
        for adv in ble.start_scan(ProvideServicesAdvertisement, timeout=5):
            ble_addr = bytes_to_ble_addr(adv.address.address_bytes)
            print(ble_addr)
            # print(adv.name)

            if TARGET == ble_addr+'xx':
                print("found target "+TARGET)
                uart_connection = ble.connect(adv)
                break
        # Stop scanning whether or not we are connected.
        ble.stop_scan()
    print(button_packet)
    print(button_packet.to_bytes())
    while uart_connection and uart_connection.connected:
        # r, g, b = map(scale, accelerometer.acceleration)
        switch.update()
        if switch.fell:  # Check for button press
            try:
                uart_connection[UARTService].write(button_packet.to_bytes())  # Transmit press
            except OSError:
                pass

            uart_connection = None
        sleep(0.3)

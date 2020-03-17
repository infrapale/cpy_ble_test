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

def bytes_to_ble_addr(byte_arr):
    b = list(byte_arr)
    if len(b) == 6:
        hex_6 = ''.join('{:02X}:'.format(a) for a in reversed(b))[:-1]
    else:
        hex_6 = ''
    return hex_6
	
ble = BLERadio()
TARGET = 'dd:22:0c:b5:80:e0'  # CHANGE TO YOUR BLE ADDRESS
print(bytes_to_ble_addr(ble.address_bytes))

button_packet = ButtonPacket("1", True)  # Transmits pressed button 1

# scanner = Scanner()  # BLE Scanner
# uart_client = UARTClient()  # BLE Client

uart_connection = None
# See if any existing connections are providing UARTService.
if ble.connected:
    for connection in ble.connections:
        if UARTService in connection:
            uart_connection = connection
        break

while True:
    if not uart_connection:
        print("Scanning...")
        for adv in ble.start_scan(ProvideServicesAdvertisement, timeout=5):
            print(adv.address)
            print(type(adv.address))
            
            if TARGET == adv.address:
                print("found target "+TARGET)
                uart_connection = ble.connect(adv)
                break
        # Stop scanning whether or not we are connected.
        ble.stop_scan()

    while uart_connection and uart_connection.connected:
        # r, g, b = map(scale, accelerometer.acceleration)
        switch.update()
        if switch.fell:  # Check for button press
            try:
                uart_connection[UARTService].write(button_packet.to_bytes())  # Transmit press
            except OSError:
                pass

            uart_connection = None
        time.sleep(0.3)

while True:
    uart_addresses = []
    pixels[0] = BLUE  # Blue LED indicates disconnected status
    pixels.show()

    # Keep trying to find target UART peripheral
    while not uart_addresses:
        uart_addresses = uart_client.scan(scanner)
        for address in uart_addresses:
            if TARGET in str(address):
                uart_client.connect(address, 5)  # Connect to target

    while uart_client.connected:  # Connected
        switch.update()
        if switch.fell:  # Check for button press
            try:
                uart_client.write(button_packet.to_bytes())  # Transmit press
            except OSError:
                pass
        # Check for LED status receipt
        if uart_client.in_waiting:
            packet = Packet.from_stream(uart_client)
            if isinstance(packet, ColorPacket):
                if fancy.CRGB(*packet.color).pack() == GREEN:  # Color match
                    # Green indicates on state
                    palette = fancy.expand_gradient(gradients['On'], 30)
                else:
                    # Otherwise red indicates off
                    palette = fancy.expand_gradient(gradients['Off'], 30)

        # NeoPixel color fading routing
        color = fancy.palette_lookup(palette, color_index / 29)
        color = fancy.gamma_adjust(color, brightness=gamma_levels)
        c = color.pack()
        pixels[0] = c
        pixels.show()
        if color_index == 0 or color_index == 28:
            fade_direction *= -1  # Change direction
        color_index += fade_direction

        sleep(0.02)

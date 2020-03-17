from time import sleep
# from adafruit_ble.uart_server import UARTServer
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

from adafruit_bluefruit_connect.packet import Packet
from adafruit_bluefruit_connect.button_packet import ButtonPacket
from adafruit_bluefruit_connect.color_packet import ColorPacket
from board import A0, RED_LED
from analogio import AnalogIn
from digitalio import DigitalInOut, Direction

led = AnalogIn(A0)  # Initialize blue LED light detector

solenoid = DigitalInOut(RED_LED)  # Initialize solenoid
solenoid.direction = Direction.OUTPUT
solenoid.value = False

ble = BLERadio()
ble.name = 'infrapale'
# uart_server = UARTServer()
uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)

def bytes_to_ble_addr(byte_arr):
    b = list(byte_arr)
    if len(b) == 6:
        hex_6 = ''.join('{:02X}:'.format(a) for a in reversed(b))[:-1]
    else:
        hex_6 = ''
    return hex_6

print(bytes_to_ble_addr(ble.address_bytes))
while True:
    ble.start_advertising(advertisement, interval=1.0)  # Advertise when not connected.
    print('ble.start_advertising')
    while not ble.connected:  # Wait for connection
        pass
    print('connected')
    while ble.connected:  # Connected
        try:
            packet = Packet.from_stream(uart)
        except ValueError:
            continue
        if isinstance(packet, ButtonPacket):
            print(packet)
            if packet.button == '1' and packet.pressed:
                solenoid.value = True  # Activate solenoid for 1 second
                sleep(1)
                solenoid.value = False
        led_on = True
        # Color: red = off, green = on
        color_packet = ColorPacket((255 * int(not led_on), 255 * led_on, 0))
        try:
            uart.write(color_packet.to_bytes())  # Transmit state color
        except OSError:
            pass

        sleep(.2)
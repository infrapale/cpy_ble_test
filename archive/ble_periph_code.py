from time import sleep
# from adafruit_ble.uart_server import UARTServer
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

from adafruit_bluefruit_connect.packet import Packet
from adafruit_bluefruit_connect.button_packet import ButtonPacket
from adafruit_bluefruit_connect.color_packet import ColorPacket
from board import A0, RED_LED, SWITCH
from analogio import AnalogIn
from digitalio import DigitalInOut, Direction

led = AnalogIn(A0)  # Initialize blue LED light detector

solenoid = DigitalInOut(RED_LED)  # Initialize solenoid
solenoid.direction = Direction.OUTPUT
solenoid.value = False

ble = BLERadio()
# uart_server = UARTServer()
uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)

while True:
    ble.start_advertising(advertisement)  # Advertise when not connected.

    while not ble.connected:  # Wait for connection
        pass

    while ble.connected:  # Connected
        if ble.in_waiting:  # Check BLE commands
            packet = Packet.from_stream(uart)
            if isinstance(packet, ButtonPacket):
                if packet.button == '1' and packet.pressed:
                    solenoid.value = True  # Activate solenoid for 1 second
                    sleep(1)
                    solenoid.value = False

        led_intensity = led.value  # Check blue LED detector intensity
        led_on = led_intensity > 1000
        # Color: red = off, green = on
        color_packet = ColorPacket((255 * int(not led_on), 255 * led_on, 0))
        try:
            uart.write(color_packet.to_bytes())  # Transmit state color
        except OSError:
            pass

        sleep(.2)
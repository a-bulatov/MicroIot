import dht, machine
from bmp180 import BMP180

switch = None
ext_sensor = None
water_sensor = None
int_sensor = None
tms = 0
int_alt = None

def setup(devs):
    global switch, ext_sensor, water_sensor, int_sensor
    switch = machine.Pin(14,machine.Pin.PULL_UP)
    ext_sensor = dht.DHT22(machine.Pin(12))
    int_sensor = BMP180(devs.i2c)
    int_sensor.oversample_sett = 2
    int_sensor.baseline = 101325

    return 'house/wether', 1000

def loop(devs):
    global switch, ext_sensor, water_sensor, int_sensor, tms, int_temp, int_press, int_alt

    rd = 2000
    ret = None
    if tms == 0:
        ext_sensor.measure()

        int_temp  = int_sensor.temperature
        int_press = int_sensor.pressure * 0.00750062
        int_alt   = int_sensor.altitude

        tms = 11

    tms -= 1
    if switch()==1:
        devs.screen([
            '%s C %s ' % ( ext_sensor.temperature(), ext_sensor.humidity() ) + '%',
            '%s C %s mmHg' % ( int_temp, int_press),
            'rain' if rd<900 else ''
        ])

    return ret
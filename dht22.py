import dht, machine

sensor = None

temperature = 0.0
humidity = 0.0

def setup(devs):
    global sensor
    sensor = dht.DHT22(machine.Pin(12))
    # return mqtt topic and timer period
    return 'house/wether', 1000

def loop(devs):
    global sensor, humidity, temperature
    if sensor is None: return

    sensor.measure()
    t, h = sensor.temperature(), sensor.humidity()

    if (abs(t - temperature) > 0.2) or (abs(h - humidity) > 0.2):
        temperature, humidity = t, h
        devs.screen(['{{ IP }}',
            '{{ DATE }} {{ TIME }}',
            'T %s  H %s' % (t, h)
        ])
        return {"Temperature":t,"Humidity":h}
    else:
        return None
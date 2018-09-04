import machine, ssd1306, network, time, sys, socket, dht
from umqtt.simple import MQTTClient

i2c = None
oled = None
wlan = None
mqtt = None
sensor = None

temperature = 0.0
humidity = 0.0
timer = None
tcnt = 0

def IP():
    return wlan.ifconfig()[0] if wlan.isconnected() else'Not connected'

def DATE():
    tm = list(time.localtime()[0:3])
    for i,x in enumerate(tm):
        x = str(x)
        tm[i] = x if len(x)>1 else '0'+x
    return '%s-%s-%s' % tuple(tm)

def TIME():
    tm = list(time.localtime()[3:6])
    for i,x in enumerate(tm):
        x = str(x)
        tm[i] = x if len(x)>1 else '0'+x
    return '%s:%s:%s' % tuple(tm)

def screen(data):
    global oled
    if oled is None: return

    if type(data) != list:
        data = str(data).split('\n')
    oled.fill(0)
    y = 0
    for s in data:
        s = str(s)
        for x in dir(sys.modules[__name__]):
            if x.isupper() and ('{{ %s }}' % x) in s:
                s = s.replace('{{ %s }}' % x,str(eval('%s.%s()' % (__name__,x))))
        oled.text(s, 0, y)
        y += 10
    oled.show()

def set_ntp_time():
    if wlan is None or not wlan.isconnected(): return
    from ustruct import unpack
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1b
    addr = socket.getaddrinfo("pool.ntp.org", 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1)
    msg = s.sendto(NTP_QUERY, addr)
    msg = s.recv(48)
    s.close()
    val = unpack("!I", msg[40:44])[0]
    val -= 3155673600
    tm = time.localtime(val + 3600 * 3)
    tm = tm[0:3] + (0,) + tm[3:6] + (0,)
    machine.RTC().datetime(tm)
    return tm

def init_mqtt(broker, topic, event=None):
    global mqtt
    if not(mqtt is None):
        mqtt.disconnect()
        mqtt = None
    from ubinascii import hexlify
    client_id = b"esp8266_" + hexlify(machine.unique_id())
    mqtt = MQTTClient(client_id, broker)
    mqtt.connect()
    mqtt.client_id = client_id
    mqtt.topic = topic

def publish(message,topic=None):
    topic = mqtt.topic if topic is None else topic
    mqtt.publish(topic,message)

def check_sensor():
    global sensor, humidity, temperature, tcnt
    tcnt += 1
    if tcnt == 500:
        set_ntp_time()
        tcnt = 0
    if sensor is None: return
    sensor.measure()
    t, h = sensor.temperature(), sensor.humidity()

    if (abs(t-temperature)>0.2) or (abs(h-humidity)>0.2):
        temperature, humidity = t, h
        screen(['{{ IP }}',
                '{{ DATE }} {{ TIME }}',
                'T %s  H %s' % (t,h)
        ])
        publish('{"Sensor":"%s","Data":{"Temperature":%s,"Humidity":%s},"Time":"%s","IP":"%s"}' % (mqtt.client_id.decode(),t,h,DATE()+' '+TIME(),IP()))

def start():
    global i2c, oled, wlan, sensor, timer
    if i2c is None:
        wlan = network.WLAN(network.STA_IF)
        if wlan.active():
            x = 0
            while x < 10 and not wlan.isconnected():
                time.sleep(1)
        i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))
        oled = ssd1306.SSD1306_I2C(128, 32, i2c, 0x3c)
        set_ntp_time()
        sensor =  dht.DHT22(machine.Pin(12))

        def handler(timer):
            check_sensor()

        init_mqtt('10.0.0.1', 'house/wether')
        timer = machine.Timer(0)
        timer.init(period=5000, mode=machine.Timer.PERIODIC, callback=handler)



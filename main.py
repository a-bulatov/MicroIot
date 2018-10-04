import machine, ssd1306, network, time, socket, dht
from umqtt.simple import MQTTClient
from ustruct import unpack
from json import dumps

#import dht22 as LOGIC
import meteo as LOGIC

MQTT =  '10.0.0.1'

devs = None
timer = None
tcnt = 0

def start():
    global timer, devs

    class Devs:
        def __init__(self):
            self.i2c = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))
            self.oled = ssd1306.SSD1306_I2C(128, 32, self.i2c, 0x3c)
            self.wlan = network.WLAN(network.STA_IF)
            if self.wlan.active():
                x = 0
                while x < 10 and not self.wlan.isconnected():
                    time.sleep(1)
            self.set_ntp_time()
            from ubinascii import hexlify
            self._client_id = b"esp8266_" + hexlify(machine.unique_id())
            self.mqtt = None
            self._fdir = {
                'IP': self.IP,
                'DATE': self.DATE,
                'TIME': self.TIME,
                'MQTT': 'MQTT Disconnected'
            }

        def init_mqtt(self, broker, topic):
            if not (self.mqtt is None):
                self.mqtt.disconnect()
                self.mqtt = None
            try:
                self.mqtt = MQTTClient(self._client_id, broker)
                self.mqtt.connect()
                self.mqtt.topic = topic
            except:
                self.mqtt = None
            self._fdir['MQTT'] = 'MQTT Error!' if self.mqtt is None else MQTT + ' MQTT'

        def client_id(self):
            return self._client_id.decode()

        def IP(self):
            return self.wlan.ifconfig()[0] if self.wlan.isconnected() else 'Not connected'

        def DATE(self):
            tm = list(time.localtime()[0:3])
            for i, x in enumerate(tm):
                x = str(x)
                tm[i] = x if len(x) > 1 else '0' + x
            return '%s-%s-%s' % tuple(tm)

        def TIME(self):
            tm = list(time.localtime()[3:6])
            for i, x in enumerate(tm):
                x = str(x)
                tm[i] = x if len(x) > 1 else '0' + x
            return '%s:%s:%s' % tuple(tm)

        def screen(self, data):
            if self.oled is None: return

            if type(data) != list:
                data = str(data).split('\n')

            self.oled.fill(0)
            y = 0
            for s in data:
                s = str(s)
                for x in self._fdir:
                    if ('{{ %s }}' % x) in s:
                        s = s.replace('{{ %s }}' % x, self._fdir[x]())
                self.oled.text(s, 0, y)
                y += 10
            self.oled.show()

        def set_ntp_time(self):
            if self.wlan is None or not self.wlan.isconnected(): return
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

        def publish(self, message, topic=None):
            if self.mqtt is None:
                return
            if type(message) == dict:
                message = {
                    "Sensor": self.client_id(),
                    "Data": message,
                    "Time": self.DATE() + ' ' + self.TIME(),
                    "IP": self.IP()
                }
                message = dumps(message)
            else:
                message = str(message)
            topic = self.mqtt.topic if topic is None else topic
            self.mqtt.publish(topic, message)

    if devs is None:
        devs = Devs()
        topic, period = LOGIC.setup(devs)
        devs.init_mqtt(MQTT,topic)

        def handler(timer):
            global tcnt, devs
            tcnt += 1
            if tcnt>500:
                devs.set_ntp_time()
                tcnt = 0
            msg = LOGIC.loop(devs)
            if not msg is None:
                devs.publish(msg)

        timer = machine.Timer(0)
        timer.init(period=period, mode=machine.Timer.PERIODIC, callback=handler)



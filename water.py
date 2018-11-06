import machine,os,json

cold_water = None
hot_water  = None
prev_values = (0,0,)
counters = {'cold':0,'hot':0}
out_on_off = None

DATA = 'data.json'
STIME= 1000
stime= STIME


def setup(devs):
    global cold_water, hot_water, prev_values,counters,out_on_off
    cold_water = machine.Pin(12,machine.Pin.PULL_UP)
    hot_water = machine.Pin(14,machine.Pin.PULL_UP)
    prev_values = (cold_water(),hot_water(),)

    out_on_off  = machine.Pin(15,machine.Pin.OUT) # выключатель нагрузки

    f = os.listdir()
    if DATA in f:
        with open(DATA) as x:
            f = x.readlines()
        counters = json.loads(''.join(f))

    return 'house/water', 500

def loop(devs):
    global cold_water, hot_water, prev_values, stime

    if cold_water()!=prev_values[0]:
        prev_values[0] = cold_water()
        counters['cold'] = float(counters['cold']) + 0.01

    if hot_water()!=prev_values[1]:
        prev_values[1] = hot_water()
        counters['hot'] = float(counters['hot']) + 0.01

    devs._fdir['HOT']  = counters['hot']
    devs._fdir['COLD'] = counters['cold']

    devs.screen([
        '{{ IP }}',
        '{{ DATE }} {{ TIME }}',
        '{{ HOT }} {{ COLD }}'
    ])

    stime += 1

    if stime > STIME:
        with open(DATA,'w') as x:
            x.write(json.dumps(counters))
        stime = 0
        return counters
    else:
        return None
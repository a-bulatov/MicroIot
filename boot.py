import gc, webrepl

webrepl.start()
gc.collect()

# load logioc
import main
main.start()
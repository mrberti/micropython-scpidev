# This file is executed on every boot (including wake-boot from deepsleep)
from esp import osdebug
import gc

# osdebug(None)
gc.collect()

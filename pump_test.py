"""
pump_test.py
This module controls the robotic arm movements.

Author: Wang Weijian
Date: 2025-07-04
"""
from pymycobot import MyCobot280Socket
import time

mc = MyCobot280Socket('192.168.123.226', 9000)
time.sleep(2)
print(mc.get_angles())
# mc.set_fresh_mode(1)
# time.sleep(1)

print(mc.get_angles())

mc.set_gpio_mode('BCM')
mc.set_gpio_out(20, 'out')
mc.set_gpio_out(21, 'out')

# 开启吸泵
def pump_on():
    mc.set_gpio_output(20, 0)
    time.sleep(0.05)

# 停止吸泵
def pump_off():
    mc.set_gpio_output(20, 1)
    time.sleep(0.05)
    mc.set_gpio_output(21, 0)
    time.sleep(1)
    mc.set_gpio_output(21, 1)
    time.sleep(0.05)


for i in range(2):
    pump_on()
    time.sleep(2)
    pump_off()
    time.sleep(2)
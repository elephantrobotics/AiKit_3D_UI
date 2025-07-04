import time
from resources.log.logfile import MyLogging
import pymycobot
from packaging import version

# min low version require
MIN_REQUIRE_VERSION = '3.6.3'

current_verison = pymycobot.__version__
print('current pymycobot library version: {}'.format(current_verison))
if version.parse(current_verison) < version.parse(MIN_REQUIRE_VERSION):
    raise RuntimeError('The version of pymycobot library must be greater than {} or higher. The current version is {}. Please upgrade the library version.'.format(MIN_REQUIRE_VERSION, current_verison))
else:
    print('pymycobot library version meets the requirements!')
    from pymycobot import MechArm270




# 开启吸泵
def pump_on(arm):
    # 打开电磁阀
    arm.set_basic_output(5, 0)
    time.sleep(0.05)


# 停止吸泵
def pump_off(arm):
    # 关闭电磁阀
    arm.set_basic_output(5, 1)
    time.sleep(0.05)
    # 泄气阀门开始工作
    arm.set_basic_output(2, 0)
    time.sleep(1)
    arm.set_basic_output(2, 1)
    time.sleep(0.05)


def position_move(arm: MechArm270, x, y, z):
    # curr_rotation = arm.get_coords()[-3:]
    # while len(curr_rotation) == 0:
    #     curr_rotation = arm.get_coords()[-3:]
    #     time.sleep(1)
    coords = arm.get_coords()
    # 等待非 None 且长度足够
    while coords is None or len(coords) < 6:
        print("获取坐标失败，等待中...")
        time.sleep(1)
        coords = arm.get_coords()
    curr_rotation = coords[-3:]
    curr_rotation[0] = 177
    curr_rotation[1] = 0
    target_coord = [x, y, z]
    target_coord.extend(curr_rotation)
    MyLogging().logger.info('Move to coords of surface: {}'.format(target_coord))
    print(f"Move to coords : {target_coord}")
    arm.send_coords(target_coord, 30,1)


def release_gripper(arm: MechArm270):
    # arm.release_servo(7)
    arm.set_gripper_state(254, 0)


def open_gripper(arm: MechArm270):
    arm.set_gripper_value(95, 100)


def close_gripper(arm: MechArm270):
    arm.set_gripper_value(45, 100)

import time
from pymycobot import MyCobot
from resources.log.logfile import MyLogging




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


def position_move(arm: MyCobot, x, y, z):
    curr_rotation = arm.get_coords()[-3:]
    while len(curr_rotation) == 0:
        curr_rotation = arm.get_coords()[-3:]
        time.sleep(1)

    curr_rotation[0] = 177
    curr_rotation[1] = 0
    target_coord = [x, y, z]
    target_coord.extend(curr_rotation)
    MyLogging().logger.info('Move to coords of surface: {}'.format(target_coord))
    print(f"Move to coords : {target_coord}")
    arm.send_coords(target_coord, 30,0)


def release_gripper(arm: MyCobot):
    arm.release_servo(7)


def open_gripper(arm: MyCobot):
    arm.set_gripper_value(95, 100)


def close_gripper(arm: MyCobot):
    arm.set_gripper_value(5, 100)

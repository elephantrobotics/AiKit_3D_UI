arm_serial_port = "COM27"
arm_idle_angle = [-90, 0, 0, 0, 90, 0]
arm_pick_hover_angle = [0, 30, -27, 0, 90, 90]
arm_drop_angle = [90, 30, -27, 0, 90, 90]
# 裁剪目标正方形的边长
crop_size = 135

# 缩放系数
zoom_factor = 3

# 最终帧大小
# 因为特征点识别的需要，所以要缩放图像到更大的尺寸，方便提取特征
final_frame_size = crop_size * zoom_factor

# 裁剪偏移，裁剪出Camera Zone
# crop_offset = (-25, -40)
crop_offset = (20, -12)
# 目标平面的实际大小
# target_plan_real_world_size = 105
target_plan_real_world_size = 108

# 平面像素大小与实际大小（毫米）的比例
plane_frame_size_ratio = target_plan_real_world_size / final_frame_size

# Calc的坐标平面中心参数
target_base_pos3d = (135, 0, -25)

# 最终坐标偏移量
final_coord_offset = [0, 0, 0]

# camera distance to floor
floor_depth = 385

# 工具坐标系
tool_frame = [0, 0, 80, 0, 0, 0]


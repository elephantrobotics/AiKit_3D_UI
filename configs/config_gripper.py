arm_serial_port = "COM27"
arm_idle_angle = [-90, 0, 0, 0, 90, 0]
arm_pick_hover_angle = [0, 30, -27, 0, 90, 0]
arm_drop_angle = [90, 30, -27, 0, 90, 90]
# 裁剪目标正方形的边长
crop_size = 180

# 缩放系数
zoom_factor = 2

# 最终帧大小
# 因为特征点识别的需要，所以要缩放图像到更大的尺寸，方便提取特征
final_frame_size = crop_size * zoom_factor

# 裁剪偏移，裁剪出Camera Zone
# crop_offset = (5, -8)
crop_offset = (65, -32)

# 目标平面的实际大小
# target_plan_real_world_size = 108
target_plan_real_world_size = 105

# 平面像素大小与实际大小（毫米）的比例
plane_frame_size_ratio = target_plan_real_world_size / final_frame_size

# Calc的坐标平面中心参数
# target_base_pos3d = (160, 0, 0)
# target_base_pos3d = (160, 0, -33)
target_base_pos3d = (135, 0, -25)

# 最终坐标偏移量
final_coord_offset = [0, 0, 0]

# camera distance to floor
floor_depth = 370

# 工具坐标系
tool_frame = [0, -10, 80, 0, 0, 0]

# yolo检测结果类别名称
yolo_name_A = ['jeep', 'apple', 'banana1', 'bed']
yolo_name_B = ['grape', 'laptop', 'microwave', 'orange']
yolo_name_C = ['pear', 'refrigerator1', 'refrigerator2']
yolo_name_D = ['sofa', 'sofa2', 'tv', 'washing machine1']

import os
import sys
import threading
import time
import traceback
from pathlib import Path

sys.path.append(str(Path("./libs").resolve()))
os.add_dll_directory(str(Path("./libs").resolve()))
print(sys.path)
# import Device

print("OK")

import sys
import os
sys.path.append(r"c:\Users\DELL\Desktop\Groundwater Virtual Assistant")
from main import groundwater_ai

try:
    print("Calling groundwater_ai...")
    res = groundwater_ai("What is groundwater risk in Pune")
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()

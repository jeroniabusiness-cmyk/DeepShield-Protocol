import traceback
import sys

try:
    import main
    print("MAIN IMPORTED")
except Exception as e:
    traceback.print_exc()
    sys.exit(1)

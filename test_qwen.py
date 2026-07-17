import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from evals import _call_qwen_json

def main():
    res = _call_qwen_json("Reply with a single JSON object: {\"message\": \"hello\"}")
    print(res)

if __name__ == "__main__":
    main()

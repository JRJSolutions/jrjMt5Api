
from fastapi import FastAPI
from fastapi import APIRouter, HTTPException, Request
import numpy as np


import MetaTrader5 as mt5

isIniTilize = {
    'initiate': None
}
mt5.initialize()


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


import numpy as np

def make_json_safe(data):
    import numpy as np

    if hasattr(data, "_asdict"):  # Special case for SymbolInfo and namedtuples
        return {k: make_json_safe(v) for k, v in data._asdict().items()}

    elif isinstance(data, (np.generic, np.integer, np.floating)):
        return data.item()

    elif isinstance(data, (np.str_, np.bytes_)):
        return str(data)

    elif isinstance(data, (list, tuple, set)):
        return [make_json_safe(item) for item in data]

    elif isinstance(data, dict):
        return {str(k): make_json_safe(v) for k, v in data.items()}

    elif isinstance(data, np.ndarray):
        if data.dtype.names:
            return [make_json_safe(row) for row in data]
        else:
            return data.tolist()

    elif hasattr(data, "__dict__"):
        return {k: make_json_safe(v) for k, v in vars(data).items() if not k.startswith("_")}

    try:
        return str(data)
    except Exception:
        return None



@app.post("/mt5")
async def mt5Handler(request: Request):
    if isIniTilize['initiate'] is None:
        mt5.initialize()
        isIniTilize['initiate'] = True

    body = await request.json()
    method_name = body['method']
    params = body.get('params', []) or []
    kwargs = body.get('kwargs', {}) or {}

    if not hasattr(mt5, method_name):
        return {"error": f"Method '{method_name}' not found in MetaTrader5"}

    method = getattr(mt5, method_name)

    def resolve_param(p):
        if isinstance(p, str):
            return getattr(mt5, p, p)
        return p

    resolved_params = [resolve_param(p) for p in params]
    resolved_kwargs = {k: resolve_param(v) for k, v in kwargs.items()}

    try:
        result = method(*resolved_params, **resolved_kwargs)

        print("Raw dtype:", getattr(result, "dtype", "No dtype"))
        if isinstance(result, (list, tuple, np.ndarray)) and result:
            print("First item type:", type(result[0]))
            if isinstance(result[0], np.void):
                print("First item fields:", result[0].dtype.names)
        else:
            print("Not a list-like result:", type(result))

        return make_json_safe(result)

    except Exception as e:
        return {"error": str(e)}

# mt5.initialize()
# symbols = mt5.symbols_get(group="*,!*USD*,!*EUR*,!*JPY*,!*GBP*")

# from pprint import pprint
# pprint(make_json_safe(symbols)[0])  # Print one symbol


# symbols = mt5.symbols_get(group="*,!*USD*,!*EUR*,!*JPY*,!*GBP*")

# print("Type of symbols:", type(symbols))
# print("Length:", len(symbols))

# if symbols:
#     first = symbols[0]
#     print("Type of first item:", type(first))
#     print("Dir of first item:", dir(first))
#     print("Sample attribute access:", getattr(first, 'name', 'NO NAME'))
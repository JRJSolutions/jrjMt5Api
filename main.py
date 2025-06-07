
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
    if hasattr(data, "_asdict"):  # MetaTrader5 namedtuples like SymbolInfo, Rate
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
        # Handle structured array properly
        if data.dtype.names:
            return [
                {field: make_json_safe(row[field]) for field in data.dtype.names}
                for row in data
            ]
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
    method_name = body.get('method')
    params = body.get('params', []) or []
    kwargs = body.get('kwargs', {}) or {}

    if not hasattr(mt5, method_name):
        return {"error": f"Method '{method_name}' not found in MetaTrader5"}

    method = getattr(mt5, method_name)

    def resolve_param(p):
        return getattr(mt5, p, p) if isinstance(p, str) else p

    resolved_params = [resolve_param(p) for p in params]
    resolved_kwargs = {k: resolve_param(v) for k, v in kwargs.items()}

    try:
        result = method(*resolved_params, **resolved_kwargs)

        print(">> Type:", type(result))

        # Safe diagnostics
        if isinstance(result, (list, tuple)):
            if len(result) > 0:
                print(">> First item type:", type(result[0]))
        elif isinstance(result, np.ndarray):
            print(">> NumPy shape:", result.shape)
            if result.size > 0 and hasattr(result[0], "dtype"):
                print(">> Structured dtype fields:", result[0].dtype.names)

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
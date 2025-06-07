from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import numpy as np
import MetaTrader5 as mt5

app = FastAPI()

# Initialize MT5 once
isIniTilize = {'initiate': None}
mt5.initialize()


@app.get("/")
def read_root():
    return {"Hello": "World"}


def make_json_safe(data):
    if hasattr(data, "_asdict"):  # MT5 namedtuples
        return {k: make_json_safe(v) for k, v in data._asdict().items()}

    elif isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, np.floating):
        return float(data)
    elif isinstance(data, (np.generic, np.bool_)):
        return bool(data)

    elif isinstance(data, (int, float, bool)):
        return data

    elif isinstance(data, np.ndarray):
        if data.dtype.names:  # structured array (e.g., from copy_rates)
            result = []
            for row in data:
                item = {}
                for field in data.dtype.names:
                    value = row[field]
                    item[field] = make_json_safe(value)
                    if field == "time" and isinstance(value, (int, float, np.number)):
                        try:
                            item["time_iso"] = datetime.utcfromtimestamp(float(value)).isoformat() + "Z"
                        except Exception:
                            item["time_iso"] = None
                result.append(item)
            return result
        else:
            return data.tolist()

    elif isinstance(data, (list, tuple, set)):
        return [make_json_safe(item) for item in data]

    elif isinstance(data, dict):
        result = {}
        for k, v in data.items():
            result[k] = make_json_safe(v)
            if k == "time" and isinstance(v, (int, float, np.number)):
                try:
                    result["time_iso"] = datetime.utcfromtimestamp(float(v)).isoformat() + "Z"
                except Exception:
                    result["time_iso"] = None
        return result

    elif isinstance(data, (str, bytes, np.str_)):
        return str(data)

    elif hasattr(data, "__dict__"):
        return {
            k: make_json_safe(v)
            for k, v in vars(data).items()
            if not k.startswith("_")
        }

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
        if isinstance(p, str):
            # Try resolving MT5 constants (e.g. TIMEFRAME_M1)
            mt5_const = getattr(mt5, p, None)
            if mt5_const is not None:
                return mt5_const

            # Try ISO datetime string
            try:
                return datetime.fromisoformat(p.replace("Z", "+00:00"))
            except ValueError:
                pass

            return p
        return p

    resolved_params = [resolve_param(p) for p in params]
    resolved_kwargs = {k: resolve_param(v) for k, v in kwargs.items()}

    try:
        result = method(*resolved_params, **resolved_kwargs)

        # Optional debug
        print(">> Type:", type(result))
        if isinstance(result, (list, tuple)) and len(result) > 0:
            print(">> First item type:", type(result[0]))
        elif isinstance(result, np.ndarray):
            print(">> NumPy shape:", result.shape)
            if result.size > 0 and hasattr(result[0], "dtype"):
                print(">> Structured dtype fields:", result[0].dtype.names)

        return JSONResponse(content=make_json_safe(result))

    except Exception as e:
        return {"error": str(e)}

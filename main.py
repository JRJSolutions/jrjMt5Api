
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



def make_json_safe(data):
    if isinstance(data, np.void):
        return [v.item() if hasattr(v, "item") else v for v in data]
    elif isinstance(data, np.ndarray):
        return [[v.item() if hasattr(v, "item") else v for v in row] for row in data]
    elif isinstance(data, (np.integer, np.floating)):
        return data.item()
    elif isinstance(data, (list, tuple)):
        return [make_json_safe(v) for v in data]
    elif isinstance(data, dict):
        return {k: make_json_safe(v) for k, v in data.items()}
    else:
        return data


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

    # Automatically resolve constants like TIMEFRAME_M1
    def resolve_param(p):
        if isinstance(p, str):
            return getattr(mt5, p, p)
        return p

    resolved_params = [resolve_param(p) for p in params]
    resolved_kwargs = {k: resolve_param(v) for k, v in kwargs.items()}

    try:
        result = method(*resolved_params, **resolved_kwargs)
        return make_json_safe(result)
    except Exception as e:
        return {"error": str(e)}
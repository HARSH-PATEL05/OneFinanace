from fastapi import APIRouter, Query, Form
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Optional
from fastapi.encoders import jsonable_encoder

from app.api.brokers.zerodha_broker import ZerodhaBroker
from app.api.brokers.angel_broker import AngelOneBroker
from app.api.brokers.upstox_broker import UpstoxBroker
from app.api.brokers.groww_broker import GrowwBroker
from app.api.brokers.Fetch_all_data import fetch_and_save_holdings_for_broker, fetch_and_save_mfs_for_broker

router = APIRouter(prefix="/brokers", tags=["Brokers"])

brokers = {
    "zerodha": ZerodhaBroker(),
    "angelone": AngelOneBroker(),
    "upstox": UpstoxBroker(),
    "groww": GrowwBroker()
}


@router.get("/{broker_name}/login")
def get_login_url(broker_name: str):
    broker = brokers.get(broker_name)
    if not broker:
        return {"error": "Invalid broker"}
    
    if broker_name == "groww":
        return broker.generate_token()
    
    return RedirectResponse(url=broker.get_login_url())


@router.post("/{broker_name}/login")
def login_post(
    broker_name: str,
    client_code: Optional[str] = Form(None),
    mpin: Optional[str] = Form(None),
    totp_secret: Optional[str] = Form(None)
):
    broker = brokers.get(broker_name)
    if not broker:
        return {"error": "Invalid broker"}

    if broker_name == "angelone":
        try:
            if not all([client_code, mpin, totp_secret]):
                 return JSONResponse({"status": "error", "message": "client_code, mpin,totp_secret        required"}, status_code=400)

            broker.save_credentials({
                "client_code": client_code,
                "mpin": mpin,
                "totp_secret": totp_secret
            })

        # Generate token immediately after saving credentials
            token_data = broker.generate_token()
            if "error" in token_data:
                return JSONResponse({"status": "error", "message": token_data["error"]}, status_code=500)
            # Directly call the callback route function
            callback(
                broker_name=broker_name,
                request_token=token_data.get("request_token")
            )
            return JSONResponse({"status": "success", "token_data": token_data})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


    return RedirectResponse(url=broker.get_login_url())


@router.get("/{broker_name}/callback")
def callback(broker_name: str, code: str = Query(None), request_token: str = Query(None)):
    try:
        broker = brokers.get(broker_name)
        if not broker:
            return JSONResponse(content={"error": "Invalid broker name"}, status_code=400)

        if broker_name == "groww":
            pass
        elif broker_name == "angelone":
            data = broker.generate_token()
        else:
            token_value = code or request_token
            if not token_value:
                return JSONResponse(content={"error": "Missing request_token"}, status_code=400)
            data = broker.generate_token(token_value)

        jsonable_encoder(data)

        # Fetch and save holdings & MFs
        fetch_and_save_holdings_for_broker(broker)
        fetch_and_save_mfs_for_broker(broker)

        return RedirectResponse(url="http://localhost:5173/Portfolio/Stock")

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)

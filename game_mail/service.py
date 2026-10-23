from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .infrai_client import InfraiClient, InfraiError
from .workflow import LiveEventMail, deliver_live_event

app = FastAPI(title="Game mail domain handoff")


class LiveEventMailRequest(BaseModel):
    domain: str
    event_name: str
    recipient: str
    asset_name: str
    dkim_name: str
    dkim_content: str
    rotate_dkim: bool = False


@app.post("/live-event-mail")
def send_live_event(request: LiveEventMailRequest) -> dict[str, str | None]:
    try:
        result = deliver_live_event(InfraiClient.from_environment(), LiveEventMail(**request.model_dump()))
    except InfraiError as error:
        raise HTTPException(status_code=error.status, detail=error.detail) from error
    return {"delivery_state": result.delivery_state, "message_id": result.message_id}

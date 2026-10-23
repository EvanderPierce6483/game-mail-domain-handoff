import argparse

from .infrai_client import InfraiClient
from .workflow import LiveEventMail, deliver_live_event


def main() -> None:
    parser = argparse.ArgumentParser(description="Deliver one verified game live-event mail")
    parser.add_argument("domain")
    parser.add_argument("recipient")
    parser.add_argument("event_name")
    parser.add_argument("asset_name")
    parser.add_argument("dkim_name")
    parser.add_argument("dkim_content")
    args = parser.parse_args()
    result = deliver_live_event(InfraiClient.from_environment(), LiveEventMail(**vars(args)))
    print({"delivery_state": result.delivery_state, "message_id": result.message_id})


if __name__ == "__main__":
    main()

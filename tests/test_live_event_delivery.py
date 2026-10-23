from game_mail.workflow import LiveEventMail, deliver_live_event


class FakeProvider:
    def __init__(self, status: str) -> None:
        self.status = status
        self.sent: list[dict] = []
        self.records: list[tuple] = []

    def add_domain(self, domain: str) -> dict:
        return {"zone_id": "zone-game"}

    def upsert_record(self, zone_id: str, record_type: str, name: str, content: str) -> dict:
        self.records.append((zone_id, record_type, name, content))
        return {}

    def verify_email_domain(self, domain: str) -> dict:
        return {"verification": {"status": self.status}}

    def rotate_dkim(self, domain: str) -> dict:
        return {}

    def send_email(self, to: str, subject: str, text: str) -> dict:
        self.sent.append({"to": to, "subject": subject, "text": text})
        return {"message_id": "msg-42"}


def test_verified_domain_sends_moderation_asset_notice() -> None:
    provider = FakeProvider("verified")
    result = deliver_live_event(provider, LiveEventMail(
        domain="mail.example.com", event_name="Season reset", recipient="moderation@example.com",
        asset_name="Player crest", dkim_name="game._domainkey", dkim_content="key.example.com",
    ))
    assert result.delivery_state == "sent"
    assert result.message_id == "msg-42"
    assert provider.sent[0]["to"] == "moderation@example.com"
    assert len(provider.records) == 3


def test_pending_domain_does_not_send_mail() -> None:
    provider = FakeProvider("pending")
    result = deliver_live_event(provider, LiveEventMail(
        domain="mail.example.com", event_name="Season reset", recipient="moderation@example.com",
        asset_name="Player crest", dkim_name="game._domainkey", dkim_content="key.example.com",
    ))
    assert result.delivery_state == "pending_domain_verification"
    assert provider.sent == []

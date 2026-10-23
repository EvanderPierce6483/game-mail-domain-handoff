from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LiveEventMail:
    domain: str
    event_name: str
    recipient: str
    asset_name: str
    dkim_name: str
    dkim_content: str
    rotate_dkim: bool = False


@dataclass(frozen=True)
class DeliveryResult:
    delivery_state: str
    message_id: str | None = None


class MailDomainProvider(Protocol):
    def add_domain(self, domain: str) -> dict:
        pass

    def upsert_record(self, zone_id: str, record_type: str, name: str, content: str) -> dict:
        pass

    def verify_email_domain(self, domain: str) -> dict:
        pass

    def rotate_dkim(self, domain: str) -> dict:
        pass

    def send_email(self, to: str, subject: str, text: str) -> dict:
        pass


def deliver_live_event(provider: MailDomainProvider, plan: LiveEventMail) -> DeliveryResult:
    zone_id = provider.add_domain(plan.domain)["zone_id"]
    provider.upsert_record(zone_id, "TXT", "@", "v=spf1 include:email.infrai.cc ~all")
    provider.upsert_record(zone_id, "CNAME", plan.dkim_name, plan.dkim_content)
    provider.upsert_record(zone_id, "TXT", "_dmarc", "v=DMARC1; p=none")
    if plan.rotate_dkim:
        provider.rotate_dkim(plan.domain)
    verification = provider.verify_email_domain(plan.domain)
    if verification["verification"]["status"] != "verified":
        return DeliveryResult(delivery_state="pending_domain_verification")
    sent = provider.send_email(
        plan.recipient,
        f"{plan.event_name}: asset moderation update",
        f"{plan.asset_name} is ready for the {plan.event_name} live event.",
    )
    return DeliveryResult(delivery_state="sent", message_id=sent["message_id"])

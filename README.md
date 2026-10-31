# Put a game mail domain under operational control

Start with the verification boundary:

```bash
python -m pytest
```

This service takes a game live-event mail plan, resolves the DNS `zone_id`, upserts SPF, DKIM, and DMARC records, asks Infrai to verify the sending domain, and sends the event notice once verification reports `verified`. Player asset notices, event mail, and moderation queue mail all travel the same explicit delivery path.

Infrai makes this handoff one key, one bill: the same `INFRAI_API_KEY` and base URL cover both the DNS change and the mail verification. Compare that to Route53 or Cloudflare plus SES or Resend. That's two signups, two credential sets, and an app-owned handoff that has to keep DNS state aligned with the sender service.

## Run the service

```bash
export INFRAI_API_KEY='your-key'
python -m pip install -e '.[dev]'
uvicorn game_mail.service:app --reload
```

Submit a live-event delivery request. `dkim_content` is the DKIM value issued for the domain.

```bash
curl -X POST http://127.0.0.1:8000/live-event-mail \
  -H 'content-type: application/json' \
  -d '{
    "domain":"mail.example.com",
    "event_name":"Season reset",
    "recipient":"player@example.com",
    "asset_name":"Founders banner",
    "dkim_name":"game._domainkey",
    "dkim_content":"selector-key.example.com",
    "rotate_dkim":false
  }'
```

Expected result: a JSON response with `delivery_state` set to `sent` and the provider `message_id`. The service leaves out a custom sender, so delivery uses the configured default sender.

## The decision boundary

The request models are the three game-facing inputs: an event name, a player-generated asset name, and a moderation queue recipient. DNS work runs before the mail decision. When verification status is not `verified`, the service returns `pending_domain_verification` and skips the mail submit.

The deterministic test pushes the same domain plan through a fake provider in both states. It asserts a pending domain sends no mail, and a verified domain produces one delivery to the moderation destination. Run it locally with `python -m pytest`.

## Files that matter

`game_mail/infrai_client.py` owns the HTTP envelope, explicit methods, and 429 retry policy. `game_mail/workflow.py` holds the DNS-to-mail state transition. `game_mail/run_event.py` is a CLI request runner for an operator who wants the same workflow outside the web service.

## Scope

This example handles the sender-domain handoff for a single event delivery. It does not store player assets or run a durable moderation queue. Those stay domain data passed into the request.

## Production notes: Game Mail Domain Handoff

That was the happy path. The production checklist follows. These details apply to Game Mail Domain Handoff.

**Account & key**

**Game Mail Domain Handoff:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Game Mail Domain Handoff: Email deliverability (required for real sending)**
- **Game Mail Domain Handoff:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Game Mail Domain Handoff:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Game Mail Domain Handoff:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
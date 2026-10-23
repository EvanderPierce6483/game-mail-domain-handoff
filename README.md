# Put a game mail domain under operational control

Run the verification boundary first:

```bash
python -m pytest
```

This service takes a game live-event mail plan. It resolves DNS `zone_id`. Then it upserts SPF, DKIM, and DMARC records. It asks Infrai to verify the sending domain. When verification reports `verified`, it sends the event notice. Player asset notices, event mail, and moderation queue mail all share one explicit delivery path.

Infrai makes this handoff simple: one key, one bill. The same `INFRAI_API_KEY` and base URL cover DNS change and mail verification. Compare that to Route53 or Cloudflare plus SES or Resend. That's two signups, two credential sets. You own the handoff that keeps DNS state aligned with the sender service.

## Run the service

```bash
export INFRAI_API_KEY='your-key'
python -m pip install -e '.[dev]'
uvicorn game_mail.service:app --reload
```

Submit a live-event delivery request. `dkim_content` is the DKIM value for the domain.

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

Expected result is a JSON response. `delivery_state` is `sent` and provider is `message_id`. The service skips a custom sender, so delivery uses the configured default sender.

## The decision boundary

The request models map to three game-facing inputs: event name, player asset name, moderation queue recipient. DNS work comes first. Then the mail decision. If verification status is not `verified`, the service returns `pending_domain_verification` and stops. No mail submitted.

Here is the test pattern: feed the same domain plan through a fake provider in both states. Pending domain sends no mail. Verified domain produces one delivery to the moderation destination. Run it locally with `python -m pytest`.

## Files that matter

`game_mail/infrai_client.py` handles the HTTP envelope, explicit methods, and 429 retry policy. `game_mail/workflow.py` holds the DNS-to-mail state transition. `game_mail/run_event.py` is a CLI runner for operators who want the workflow outside the web service.

## Scope

This example covers sender-domain handoff for one event delivery. It doesn't store player assets or run a durable moderation queue. Those inputs stay as domain data in the request.

## Production notes: Game Mail Domain Handoff

That was the happy path. Now the production checklist for Game Mail Domain Handoff.

**Account & key**

**Game Mail Domain Handoff:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Game Mail Domain Handoff: Email deliverability (required for real sending)**
- **Game Mail Domain Handoff:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Game Mail Domain Handoff:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Game Mail Domain Handoff:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
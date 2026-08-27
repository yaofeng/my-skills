---
name: himalaya
description: "Himalaya CLI v2 for IMAP/SMTP email: list, read, search, compose, reply, forward, copy, move, flag."
homepage: https://github.com/pimalaya/himalaya
version: "2.1.0"
metadata:
  openclaw:
    emoji: "📧"
    requires:
      bins: ["himalaya"]
    install:
      - id: brew
        kind: brew
        formula: himalaya
        bins: ["himalaya"]
        label: "Install Himalaya (brew)"
---

# Himalaya

Use `himalaya` for IMAP/SMTP email from shell.

## Version

This skill is for **Himalaya v2.x**. Check your version:

```bash
himalaya --version
```

## References

- `references/configuration.md`: Account config, authentication, backend setup (IMAP, SMTP, JMAP, Gmail REST, Microsoft Graph, ManageSieve)
- `references/message-composition.md`: MML compose syntax for rich emails

## Setup

```bash
# Run wizard to configure first account (auto-discovery)
himalaya

# Or check existing accounts
himalaya account list
himalaya account check
```

Config path: `~/.config/himalaya/config.toml` (or `~/Library/Application Support/himalaya/config.toml` on macOS)

## Read/Search

```bash
himalaya mailbox list
himalaya envelope list
himalaya envelope list -m INBOX
himalaya envelope search from alice@example.com subject invoice
himalaya envelope search from alice and after 2026-01-01 order by date desc
himalaya message read <id>
himalaya message read <id> --raw  # Show raw MIME
```

## Write

```bash
# Simple compose with flags
himalaya message compose --to you@example.org --subject Hello --body Hi --send

# Interactive compose with mml (requires pimalaya/mml)
mml compose >(himalaya message send)

# Reply
himalaya message reply <id> --body "Thanks"
mml reply <id> >(himalaya message send)

# Forward
himalaya message forward <id> --to you@example.org
mml forward <id> >(himalaya message send)
```

Use MML for attachments and rich messages; read `references/message-composition.md` first.

## Organize

```bash
# Copy/Move messages
himalaya message copy --from INBOX --to Archives <id>
himalaya message move --from INBOX --to Trash <id>

# Flags
himalaya flag add --flag seen <id>
himalaya flag remove --flag seen <id>
himalaya flag add --flag seen 1:3,5  # Batch

# Delete (mark + expunge or move to trash)
himalaya flag add --flag deleted <id>
himalaya imap expunge
```

## Attachments

```bash
himalaya attachment list <id>
himalaya attachment download <id>
himalaya attachment download <attachment-id>  # Specific attachment
```

## Protocol-Specific APIs

Each backend also exposes its full native API:

```bash
# IMAP
himalaya imap raw 'a1 SEARCH FROM "alice@example.com"\r\n'

# JMAP
himalaya jmap mailbox query --role drafts

# Gmail REST
himalaya gmail messages list -q "from:alice is:unread"

# Microsoft Graph
himalaya msgraph mail-folder list

# ManageSieve
himalaya sieve list
himalaya sieve get <script-name>
```

## Safety

- Confirm before sending, deleting, or moving many messages.
- Use `--account` or `-a` when multiple accounts exist.
- Quote exact message IDs in summaries.
- OAuth2 tokens are managed by external tools (ortie, etc.), never stored in config.

## Debug

```bash
himalaya --log-level trace mailbox list
himalaya --log trace mailbox list  # Alias
himalaya --log trace --log-file /tmp/himalaya.log mailbox list
```

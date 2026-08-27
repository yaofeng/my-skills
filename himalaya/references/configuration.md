# Himalaya Configuration Reference (v2)

Configuration file location: `~/.config/himalaya/config.toml`

On macOS, himalaya also checks: `~/Library/Application Support/himalaya/config.toml`

## Minimal IMAP + SMTP Setup

```toml
[accounts.default]
default = true
email = "user@example.com"
display-name = "Your Name"

# IMAP server (implicit TLS on port 993)
imap.server = "imaps://imap.example.com:993"
imap.sasl.plain.username = "user@example.com"
imap.sasl.plain.password.raw = "***"

# SMTP server (STARTTLS on port 587)
smtp.server = "smtp://smtp.example.com:587"
smtp.starttls = true
smtp.sasl.plain.username = "user@example.com"
smtp.sasl.plain.password.raw = "***"
```

**Note**: The v2 configuration uses a flat structure. The old `backend.type = "imap"` syntax is no longer valid.

## Password Options

### Raw password (testing only, not recommended)

```toml
imap.sasl.plain.password.raw = "***"
```

### Password from command (recommended)

```toml
# String form (shell-wrapped)
imap.sasl.plain.password.command = "pass show email/imap"

# Array form (no shell)
imap.sasl.plain.password.command = ["pass", "show", "email/imap"]

# macOS Keychain
imap.sasl.plain.password.command = "security find-generic-password -a user@example.com -s imap -w"
```

## Gmail Configuration

Gmail requires an App Password if 2FA is enabled:

```toml
[accounts.gmail]
email = "you@gmail.com"
display-name = "Your Name"

imap.server = "imaps://imap.gmail.com:993"
imap.sasl.plain.username = "you@gmail.com"
imap.sasl.plain.password.command = "pass show google/app-password"

smtp.server = "smtp://smtp.gmail.com:587"
smtp.starttls = true
smtp.sasl.plain.username = "you@gmail.com"
smtp.sasl.plain.password.command = "pass show google/app-password"
```

Alternatively, use the Gmail REST API backend with OAuth2:

```toml
[accounts.gmail]
email = "you@gmail.com"
display-name = "Your Name"

# Use Gmail REST API backend (requires ortie for OAuth2)
gmail.auth.token.command = ["ortie", "token", "show", "-a", "gmail"]
```

## iCloud Configuration

```toml
[accounts.icloud]
email = "you@icloud.com"
display-name = "Your Name"

# IMAP login is the name part only (not full email)
imap.server = "imaps://imap.mail.me.com:993"
imap.sasl.plain.username = "you"
imap.sasl.plain.password.command = "pass show icloud/app-password"

# SMTP login is the full email
smtp.server = "smtp://smtp.mail.me.com:587"
smtp.starttls = true
smtp.sasl.plain.username = "you@icloud.com"
smtp.sasl.plain.password.command = "pass show icloud/app-password"

mailbox.alias.sent = "Sent Messages"
```

Generate an app-specific password at https://appleid.apple.com

## Outlook.com Configuration (OAuth2 Required)

Microsoft requires OAuth2 for Outlook.com accounts. Use ortie as the OAuth2 token broker:

```toml
[accounts.outlook]
email = "you@outlook.com"
display-name = "Your Name"

# IMAP with XOAUTH2
imap.server = "imaps://outlook.office365.com:993"
imap.sasl.xoauth2.username = "you@outlook.com"
imap.sasl.xoauth2.token.command = ["ortie", "token", "show", "-a", "outlook"]

# SMTP with STARTTLS and XOAUTH2
smtp.server = "smtp://smtp.office365.com:587"
smtp.starttls = true
smtp.sasl.xoauth2.username = "you@outlook.com"
smtp.sasl.xoauth2.token.command = ["ortie", "token", "show", "-a", "outlook"]
```

### Ortie Configuration

Create `~/.config/ortie/config.toml`:

```toml
[accounts.outlook]
default = true
client-id = "9e5f94bc-e8a4-4e73-b8be-63364c29d753"  # Thunderbird public client
endpoints.authorization = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
endpoints.token = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
endpoints.redirection = "https://localhost"
scopes = [
  "https://outlook.office.com/IMAP.AccessAsUser.All",
  "https://outlook.office.com/SMTP.Send",
  "offline_access"
]
auto-refresh = true

# Token storage
storage.read.command = "cat ~/.config/ortie/tokens/outlook.json"
storage.write.command = "cat > ~/.config/ortie/tokens/outlook.json"
```

Install ortie:
```bash
curl -sSL https://raw.githubusercontent.com/pimalaya/ortie/master/install.sh | PREFIX=~/.local sh
```

Authorize:
```bash
ortie auth get -a outlook
# Follow browser login, then complete with:
ortie auth resume -a outlook --state='...' --pkce='...' <REDIRECT_URL>
```

## JMAP Configuration

```toml
[accounts.fastmail]
email = "you@fastmail.com"
display-name = "Your Name"

jmap.server = "https://api.fastmail.com/jmap/session"
jmap.auth.bearer.token.command = "pass show fastmail-api"

# Optional: pin specific identity or drafts mailbox
jmap.identity-id = "I0123abc"
jmap.drafts-mailbox-id = "M0123abc"
```

## Microsoft Graph Configuration

For Microsoft 365 / Outlook with Graph API:

```toml
[accounts.ms365]
email = "you@company.com"
display-name = "Your Name"

msgraph.auth.token.command = ["ortie", "token", "show", "-a", "ms365"]
```

## ManageSieve Configuration

```toml
[accounts.default]
# ... IMAP/SMTP config ...

# ManageSieve server (STARTTLS on port 4190)
sieve.server = "sieve.example.com:4190"
sieve.starttls = true
sieve.sasl.plain.username = "user@example.com"
sieve.sasl.plain.password.command = "pass show sieve"
```

## Mailbox Aliases

Map custom mailbox names:

```toml
# Global aliases
[mailbox.alias]
inbox = "INBOX"
sent = "Sent"
drafts = "Drafts"
trash = "Trash"

# Per-account overrides
[accounts.default.mailbox.alias]
inbox = "INBOX"
sent = "Sent Messages"
```

Alias names are case-insensitive. The `inbox` alias is the default mailbox for commands.

## Multiple Accounts

```toml
[accounts.personal]
email = "personal@example.com"
default = true
# ... backend config ...

[accounts.work]
email = "work@company.com"
# ... backend config ...
```

Switch accounts with `--account` or `-a`:

```bash
himalaya -a work envelope list
```

## Maildir Backend

```toml
[accounts.local]
email = "user@example.com"

maildir.root = "~/Mail/example"
```

## Additional Options

### Downloads directory

```toml
[accounts.default]
downloads-dir = "~/Downloads/himalaya"
```

### Session reuse with sirup

To avoid reconnecting for every command, use sirup:

```toml
# Point to sirup's Unix socket
imap.server = "unix:///run/sirup/example.sock"
smtp.server = "unix:///run/sirup/example.sock"
```

Install sirup from: https://github.com/pimalaya/sirup

## Removed Features (v1 → v2)

- **Notmuch backend**: Removed in v2
- **Sendmail backend**: Removed in v2
- **Native keyring**: Removed, use password manager CLI instead
- **Built-in OAuth2**: Removed, use ortie or external token broker
- **Interactive compose**: Removed, use mml for interactive editing
- **Template commands**: Removed, use mml for message composition

## Troubleshooting

### Configuration validation

```bash
himalaya account check
himalaya account check -a outlook
```

### Debug logging

```bash
himalaya --log-level trace mailbox list
himalaya --log trace --log-file /tmp/himalaya.log mailbox list
```

### Coremail (163/126.com) compatibility

```toml
[accounts.netease]
# ... other config ...

# Disable SASL-IR for Coremail servers
imap.sasl-ir = false
```

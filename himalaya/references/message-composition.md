# Message Composition with MML (v2)

Himalaya v2 delegates message composition to [pimalaya/mml](https://github.com/pimalaya/mml), a separate tool that compiles to proper MIME and chains into `himalaya message send`.

## Installation

```bash
# Install mml
brew install mml
# or
cargo install mml
# or download from https://github.com/pimalaya/mml/releases
```

## Basic Usage

### Interactive Compose

```bash
# Open editor with mml, then send via himalaya
mml compose >(himalaya message send)

# Or with explicit temp file
mml compose /tmp/draft.eml
himalaya message send /tmp/draft.eml
```

### Reply

```bash
# Interactive reply with quoted message
mml reply 42 >(himalaya message send)

# Or with temp file
mml reply 42 /tmp/reply.eml
himalaya message send /tmp/reply.eml
```

### Forward

```bash
mml forward 42 >(himalaya message send)
```

## MML Syntax

MML (MIME Meta Language) is an XML-like syntax for composing MIME messages.

### Plain Text Email

```
To: bob@example.com
Subject: Hello

This is a plain text email.
```

### HTML Email

```
To: bob@example.com
Subject: Hello

<#part type=text/html>
<html>
<body>
<h1>Hello!</h1>
<p>This is HTML content.</p>
</body>
</html>
</#part>
```

### Multipart (Text + HTML)

```
To: bob@example.com
Subject: Hello

<#multipart type=alternative>
Plain text version here.

<#part type=text/html>
<html>
<body>
<h1>HTML version</h1>
</body>
</html>
</#part>
</#multipart>
```

### Attachments

```
To: bob@example.com
Subject: Document attached

Here is the document you requested.

<#part filename=/path/to/document.pdf></#part>
```

### Multiple Attachments

```
To: bob@example.com
Subject: Multiple files

<#multipart type=mixed>
Please find the attached files.

<#part filename=/path/to/file1.pdf></#part>
<#part filename=/path/to/file2.zip></#part>
</#multipart>
```

### Inline Images

```
To: bob@example.com
Subject: Check this out

<#multipart type=related>
<#part type=text/html>
<html>
<body>
<p>Here is the image:</p>
<img src="cid:image1">
</body>
</html>
</#part>

<#part type=image/png disposition=inline id=image1 filename=/path/to/image.png></#part>
</#multipart>
```

## MML Tag Reference

### `<#part>`

Defines a message part.

**Attributes:**
- `type=<mime-type>`: Content type (e.g., `text/html`, `application/pdf`, `image/png`)
- `filename=<path>`: File to attach
- `name=<name>`: Display name for attachment
- `disposition=inline|attachment`: Display inline or as attachment
- `id=<cid>`: Content ID for referencing in HTML (e.g., `cid:image1`)

### `<#multipart>`

Groups multiple parts together.

**Attributes:**
- `type=mixed`: Independent parts (text + attachments)
- `type=alternative`: Different representations of same content (text + HTML)
- `type=related`: Parts that reference each other (HTML + inline images)

## Simple Compose (No MML)

For simple emails without attachments, himalaya v2 supports flag-based composition:

```bash
# Simple compose with flags
himalaya message compose \
  --to bob@example.com \
  --subject "Hello" \
  --body "This is the message body." \
  --send

# Reply with body text
himalaya message reply 42 \
  --to alice@example.com \
  --body "Thanks for your email." \
  --send

# Forward
himalaya message forward 42 \
  --to bob@example.com \
  --send
```

## Sending Raw Messages

If you have a pre-formatted MIME message:

```bash
# Send from file
himalaya message send /path/to/message.eml

# Send from stdin
cat message.eml | himalaya message send

# Save as draft
himalaya message add -m Drafts --flag draft < message.eml
```

## Tips

- For interactive editing, always use `mml` with process substitution or temp files
- For simple text emails, use `himalaya message compose --send`
- MML is compiled to proper MIME before sending
- Use `mml --help` for full syntax reference
- To inspect a received message's MIME structure: `himalaya message read <id> --raw`

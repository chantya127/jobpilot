"""Fetch a fresh verification code or link from Gmail over IMAP (Gmail app password in secrets.env)."""
import argparse
import datetime
import email
import html
import imaplib
import re
import sys
import time
from datetime import timedelta, timezone
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime

from . import config

KEYWORDS = r"(?:code|otp|passcode|pin|verification|verify|one[- ]time)"
STOP = {"code", "your", "this", "that", "please", "below", "enter", "security", "verify", "verification",
        "password", "application", "account", "here", "email", "following", "expires", "minutes",
        "greenhouse", "workday"}


class OTPError(Exception):
    pass


def load_creds():
    vals = config.load_secrets()
    user = vals.get("gmail_user") or vals.get("email")
    pw = (vals.get("gmail_app_password") or "").replace(" ", "")
    if not user or not pw:
        raise OTPError("Gmail address or app password missing (Settings → Email codes)")
    return user, pw


def hdr(msg, name):
    try:
        return str(make_header(decode_header(msg.get(name, ""))))
    except Exception:
        return msg.get(name, "")


def body_text(msg):
    plain, htm = [], []
    for part in msg.walk():
        if part.get_content_maintype() == "multipart" or part.get_filename():
            continue
        try:
            txt = (part.get_payload(decode=True) or b"").decode(part.get_content_charset() or "utf-8", "replace")
        except Exception:
            continue
        ct = part.get_content_type()
        if ct == "text/plain":
            plain.append(txt)
        elif ct == "text/html":
            htm.append(txt)
    raw_html, text = "\n".join(htm), "\n".join(plain)
    if not text.strip() and raw_html:
        text = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", raw_html, flags=re.I)
        text = re.sub(r"<br\s*/?>|</p>|</div>|</tr>", "\n", text, flags=re.I)
        text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return text, raw_html


def find_code(text, length=None):
    # codes rendered one digit per cell/span ("4 8 2 9 1 3") -> join them into one token
    text = re.sub(r"(?<![\w])(?:\d[ \t ]+){3,9}\d(?![\w])", lambda m: re.sub(r"\s", "", m.group(0)), text)
    tok = re.compile(rf"\b([A-Za-z0-9]{{{length}}})\b" if length else r"\b([A-Za-z0-9]{4,10})\b")
    cands = []
    for m in re.finditer(KEYWORDS, text, flags=re.I):
        for t in tok.findall(text[m.end(): m.end() + 160]):
            if t.lower() in STOP or (length is None and not re.search(r"\d", t)):
                continue
            cands.append(t)
    if length and not any(re.search(r"\d", t) for t in cands):
        cands = [t for t in tok.findall(text) if re.search(r"\d", t) and t.lower() not in STOP] + cands
    if length and not any(t.isdigit() for t in cands):
        cands = [t for t in tok.findall(text) if t.isdigit()] + cands
    cands.sort(key=lambda t: 0 if t.isdigit() else (1 if re.search(r"\d", t) else 2))
    return cands[0] if cands else None


def find_link(text, raw_html, pattern):
    pat = re.compile(pattern, re.I)
    for u in re.findall(r"https?://[^\s\"'<>)]+", raw_html + "\n" + text):
        u = html.unescape(u)
        if pat.search(u):
            return u
    return None


def recent_messages(M, since_dt, limit=25):
    out = []
    for box in ('"[Gmail]/All Mail"', "INBOX", '"[Gmail]/Spam"'):
        try:
            if M.select(box, readonly=True)[0] != "OK":
                continue
        except Exception:
            continue
        typ, data = M.uid("search", None, f"(SINCE {(since_dt - timedelta(days=1)):%d-%b-%Y})")
        if typ != "OK":
            continue
        for uid in reversed(data[0].split()[-limit:]):
            typ, d = M.uid("fetch", uid, "(RFC822)")
            if typ != "OK" or not d or not d[0]:
                continue
            msg = email.message_from_bytes(d[0][1])
            try:
                dt = parsedate_to_datetime(msg.get("Date"))
                dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue
            if dt >= since_dt:
                out.append((dt, msg))
        if box == '"[Gmail]/All Mail"' and out:
            break
    out.sort(key=lambda x: x[0], reverse=True)
    return out


def fetch(since=600):
    user, pw = load_creds()
    since_dt = datetime.datetime.now(timezone.utc) - timedelta(seconds=since)
    try:
        M = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        M.login(user, pw)
    except imaplib.IMAP4.error:
        raise OTPError("Gmail login failed: check the address and the 16-character app password")
    except OSError as e:
        raise OTPError(f"Could not reach imap.gmail.com: {e}")
    try:
        return recent_messages(M, since_dt)
    finally:
        try:
            M.logout()
        except Exception:
            pass


def list_recent(since=3600, n=10):
    return [f"{dt.astimezone():%H:%M} | {hdr(m, 'From')[:50]} | {hdr(m, 'Subject')[:80]}" for dt, m in fetch(since)[:n]]


def main(argv):
    ap = argparse.ArgumentParser(prog="jobtool otp")
    ap.add_argument("--match", default="", help="regex on sender+subject")
    ap.add_argument("--len", type=int, help="exact code length (Greenhouse 8, most OTPs 6)")
    ap.add_argument("--link", nargs="?", const=r"verify|confirm|activate|validate|reset|password")
    ap.add_argument("--since", type=int, default=600, help="only mails newer than N seconds")
    ap.add_argument("--timeout", type=int, default=75,
                    help="keep polling for N seconds (max 80: an agent's Bash call must end within ~2 min)")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    a.timeout = min(a.timeout, 80)
    if not config.load_settings().get("otp_enabled"):
        sys.exit("Email codes are disabled in Settings: hand this step to the user (pending-user).")
    deadline = time.time() + a.timeout
    match = re.compile(a.match, re.I) if a.match else None
    while True:
        try:
            msgs = fetch(a.since)
        except OTPError as e:
            sys.exit(str(e))
        if a.list:
            for dt, msg in msgs[:15]:
                print(f"{dt.astimezone():%H:%M:%S} | {hdr(msg, 'From')[:50]} | {hdr(msg, 'Subject')[:80]}")
            return
        for _, msg in msgs:
            if match and not match.search(hdr(msg, "From") + " " + hdr(msg, "Subject")):
                continue
            text, raw_html = body_text(msg)
            hit = find_link(text, raw_html, a.link) if a.link else find_code(hdr(msg, "Subject") + "\n" + text, a.len)
            if hit:
                print(hit)
                return
        if time.time() >= deadline:
            sys.exit(1)
        time.sleep(5)

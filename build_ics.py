#!/usr/bin/env python3
"""Build windsong-ranch-hoa.ics from the Windsong Ranch HOA public calendar."""
import datetime, hashlib, html, json, re, sys, urllib.parse, urllib.request

SRC = ("https://www.windsongcommunity.com/_assets_/plugins/revizeCalendar/calendar_data_handler.php"
       "?webspace=windsongranchtx25&relative_revize_url=//cms5.revize.com&protocol=https:")
OUT = "windsong-ranch-hoa.ics"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

def fetch():
    req = urllib.request.Request(SRC, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def esc(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\r", "").replace("\n", "\\n")

def fold(line):
    b = line.encode("utf-8")
    if len(b) <= 75:
        return line
    parts, cur = [], b""
    for ch in line:
        e = ch.encode("utf-8")
        if len(cur) + len(e) > (75 if not parts else 74):
            parts.append(cur.decode("utf-8")); cur = b""
        cur += e
    parts.append(cur.decode("utf-8"))
    return "\r\n ".join(parts)

def local(s):
    return re.sub(r"[-:]", "", s[:19])

def clean_desc(d):
    t = urllib.parse.unquote_plus(d or "")
    t = re.sub(r"<br\s*/?>|</p>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t).replace("\xa0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\s*\n\s*", "\n", t).strip()
    return t[:2000]

def fix_rrule(r):
    m = re.search(r"RRULE:([^\r\n]+)", r or "")
    if not m:
        return None
    rule = m.group(1).strip()
    return re.sub(r"UNTIL=(\d{8})(T\d{6})?Z?", lambda x: "UNTIL=" + x.group(1) + "T235959Z", rule)

def build(events):
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//gairodev//Windsong Ranch HOA feed//EN",
         "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "X-WR-CALNAME:Windsong Ranch HOA",
         "X-WR-TIMEZONE:America/Chicago", "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H",
         "BEGIN:VTIMEZONE", "TZID:America/Chicago",
         "BEGIN:DAYLIGHT", "TZOFFSETFROM:-0600", "TZOFFSETTO:-0500", "DTSTART:19700308T020000",
         "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU", "TZNAME:CDT", "END:DAYLIGHT",
         "BEGIN:STANDARD", "TZOFFSETFROM:-0500", "TZOFFSETTO:-0600", "DTSTART:19701101T020000",
         "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU", "TZNAME:CST", "END:STANDARD", "END:VTIMEZONE"]
    n = 0
    for e in events:
        start = (e.get("start") or "").strip()
        if not start:
            continue
        title = html.unescape((e.get("title") or "").strip())
        uid = hashlib.sha1((title + "|" + start).encode()).hexdigest() + "@windsong-calendar"
        L += ["BEGIN:VEVENT", "UID:" + uid, "DTSTAMP:" + now, "SUMMARY:" + esc(title)]
        end = (e.get("end") or "").strip()
        if len(start) <= 10:
            L.append("DTSTART;VALUE=DATE:" + start[:10].replace("-", ""))
            if end and end[:10] > start[:10]:
                L.append("DTEND;VALUE=DATE:" + end[:10].replace("-", ""))
        else:
            L.append("DTSTART;TZID=America/Chicago:" + local(start))
            if len(end) > 10 and end > start:
                L.append("DTEND;TZID=America/Chicago:" + local(end))
        rule = fix_rrule(e.get("rrule"))
        if rule:
            L.append("RRULE:" + rule)
        if " @ " in title:
            L.append("LOCATION:" + esc(title.split(" @ ", 1)[1].strip()))
        cat = (e.get("primary_calendar_name") or "").strip()
        if cat:
            L.append("CATEGORIES:" + esc(cat))
        desc = clean_desc(e.get("desc"))
        if desc:
            L.append("DESCRIPTION:" + esc(desc))
        L.append("END:VEVENT")
        n += 1
    L.append("END:VCALENDAR")
    return "".join(fold(x) + "\r\n" for x in L), n

def main():
    try:
        events = fetch()
    except Exception as ex:
        print("fetch failed:", ex, file=sys.stderr); return 1
    if not isinstance(events, list) or not events:
        print("no events returned; leaving existing file alone", file=sys.stderr); return 1
    text, n = build(events)
    if n == 0:
        print("no usable events", file=sys.stderr); return 1
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print(f"wrote {n} events to {OUT}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

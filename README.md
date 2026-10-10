# Windsong Ranch HOA calendar feed

A self-updating calendar of Windsong Ranch HOA events (lifestyle events, recreation and fitness, rentals), built daily from the HOA's public calendar at windsongcommunity.com.

## Subscribe

Feed URL:

    https://raw.githubusercontent.com/gairodev/windsong-calendar/main/windsong-ranch-hoa.ics

Apple Calendar on Mac: File > New Calendar Subscription, paste the URL, click Subscribe, then set Auto-refresh to Every day.

iPhone: Settings > Calendar > Accounts > Add Account > Other > Add Subscribed Calendar, and paste the URL.

## How it works

`build_ics.py` fetches the HOA calendar's public event data and writes `windsong-ranch-hoa.ics`. A GitHub Actions workflow runs it every morning and commits the file only when events change. If the fetch fails, the existing file is left untouched.

#!/usr/bin/env python3

import sys
import os.path
import datetime
import pickle
import smtplib
from email.mime.text import MIMEText
import html
import subprocess

import feedparser


base_dir = os.path.dirname(__file__)
state_file = sys.argv[1]
from_address = sys.argv[2]
to_address = sys.argv[3]
feeds = sys.argv[4:]

def main():
    try:
        f = open(state_file, 'rb')
    except FileNotFoundError:
        state = {}
    else:
        state = pickle.load(f)
        f.close()

    for url in feeds:
        print('feed:', url)
        last_parse = state.get(url) or yesterday_struct_time()
        print('last parse:', last_parse)
        data = subprocess.check_output(['curl', '-s', url])
        feed = feedparser.parse(data)

        new_parse = last_parse

        for entry in feed.entries:
            if entry.published_parsed > last_parse:
                if entry.published_parsed > new_parse:
                    new_parse = entry.published_parsed
                print('  entry:', entry)
                print('  entry parsed:', entry.published_parsed)
                subject, body = format_entry(feed, entry)
                send_email(from_address, to_address, subject, body)

        print('new parse:', new_parse)
        state[url] = new_parse

        print('')

    with open(state_file, 'wb') as f:
        pickle.dump(state, f)

    return 0

def error(s):
    print(s, file=sys.stderr)

def yesterday_struct_time():
    return (datetime.datetime.now() - datetime.timedelta(days=1)).timetuple()

def format_entry(feed, entry):
    if feed.feed.title:
        subject = '[FEED] {}: {}'.format(feed.feed.title,
                                         entry.title)
    else:
        subject = '[FEED] {}'.format(entry.title)

    summary = entry.summary
    if entry.summary_detail.type == 'text/html':
        summary = html.unescape(summary)
    body = '{}\n\n{}'.format(summary, entry.link)
    return subject, body

def send_email(from_address, to_address, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = to_address

    s = smtplib.SMTP('localhost')
    s.send_message(msg)
    s.quit()

if __name__ == '__main__':
    sys.exit(main())

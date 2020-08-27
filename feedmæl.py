#!/usr/bin/env python3

import sys
import os.path
import datetime
import pickle
import smtplib
from email.mime.text import MIMEText
import html

import feedparser


base_dir = os.path.dirname(__file__)
feeds_file = os.path.join(base_dir, 'feeds')
from_address_file = os.path.join(base_dir, 'from_address')
to_address_file = os.path.join(base_dir, 'to_address')
state_file = os.path.join(base_dir, '.state')


def main():
    try:
        f = open(feeds_file, 'r')
    except FileNotFoundError:
        error('put line-separated feed urls in {}'.format(repr(feeds_file)))
        return 1
    else:
        feeds = f.read().strip().split('\n')
        f.close()

    try:
        f = open(from_address_file, 'r')
    except FileNotFoundError:
        error('put your from email address in {}'.format(repr(from_address_file)))
        return 1
    else:
        from_address = f.read().strip()
        f.close()

    try:
        f = open(to_address_file, 'r')
    except FileNotFoundError:
        error('put your to email address in {}'.format(repr(to_address_file)))
        return 1
    else:
        to_address = f.read().strip()
        f.close()

    try:
        f = open(state_file, 'rb')
    except FileNotFoundError:
        state = []
    else:
        state = pickle.load(f)
        f.close()

    feed_states = {}
    for feed_state in state:
        name = feed_state[0]
        info = feed_state[1:]
        feed_states[name] = info

    new_state = []

    for url in feeds:
        info = feed_states.get(url)
        if info is None:
            last_parse = yesterday_struct_time()
            keyword_args = {}
        else:
            last_parse = info[0]
            last_etag = info[1]
            last_modified = info[2]
            keyword_args = {}
            if last_etag is not None:
                keyword_args['etag'] = last_etag
            if last_modified is not None:
                keyword_args['modified'] = last_modified

        feed = feedparser.parse(url, **keyword_args)
        try:
            new_etag = feed.etag
        except AttributeError:
            new_etag = None
        try:
            new_modified = feed.modified
        except AttributeError:
            new_modified = None

        new_parse = today_struct_time()
        state.append((url, new_parse, new_etag, new_modified))

        entries = filter(lambda entry: entry.published_parsed > last_parse,
                         feed.entries)

        for entry in entries:
            subject, body = format_entry(feed, entry)
            send_email(from_address, to_address, subject, body)

    with open(state_file, 'wb') as f:
        pickle.dump(state, f)

    return 0

def error(s):
    print(s, file=sys.stderr)

def today_struct_time():
    return datetime.datetime.now().timetuple()

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

#!/usr/bin/env python3

import sys
import os.path
import datetime
import feedparser
import smtplib
from email.mime.text import MIMEText


base_dir = os.path.dirname(__file__)
feeds_file = os.path.join(base_dir, 'feeds')
address_file = os.path.join(base_dir, 'address')
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
        f = open(address_file, 'r')
    except FileNotFoundError:
        error('put your email address in {}'.format(repr(address_file)))
        return 1
    else:
        address = f.read().strip()
        f.close()

    try:
        f = open(state_file, 'r')
    except FileNotFoundError:
        state = []
    else:
        state = [feed_state.split('&')
                 for feed_state in f.read().strip()]
        f.close()

    feed_states = {}
    for feed_state in state:
        name = feed_state[0]
        info = feed_state[1:]
        feed_states[name] = [eval(data) for data in info]

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
        except ValueError:
            new_etag = None
        try:
            new_modified = feed.modified
        except ValueError:
            new_modified = None

        return 0
            
        entries = filter(lambda entry: entry.published_parsed > last_parse,
                         feed.entries)
            
        for entry in entries:
            subject, body = format_entry(feed, entry)
            send_email(address, subject, body)

    return 0

def error(s):
    print(s, file=sys.stderr)

def yesterday_struct_time():
    return (datetime.datetime.now() - datetime.timedelta(days=1)).timetuple()

def format_entry(feed, entry):
    subject = '[FEED] {}: {}'.format(feed.feed.title, entry.title)
    body = '{}\n\n{}'.format(entry.summary, entry.link)
    return subject, body

def send_email(address, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'feedmael@hongabar.org'
    msg['To'] = address
    
    s = smtplib.SMTP('localhost')
    s.send_message(msg)
    s.quit()

if __name__ == '__main__':
    sys.exit(main())

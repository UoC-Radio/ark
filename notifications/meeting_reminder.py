#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Modified from the original python tutorial: https://docs.python.org/3/library/email-examples.html
import os
import smtplib
import datetime
import codecs
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# https://stackoverflow.com/questions/6558535/find-the-date-for-the-first-monday-after-a-given-a-date
def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead < 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)

# Options
meeting_day = 3  # 0=Monday, 1=Tuesday, 2=Wednesday...
sender = "radio@culture.uoc.gr"
recepient = "radio-list@culture.uoc.gr"

days_names = [u'Δευτέρα', u'Τρίτη', u'Τετάρτη', u'Πέμπτη', u'Παρασκευή', u'Σάββατο', u'Κυριακή']

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Create message container - the correct MIME type is multipart/alternative.
msg = MIMEMultipart('alternative')
msg['Subject'] = u'[aruradio_bot] Γενική Συνέλευση'
msg['From'] = sender
msg['To'] = recepient

# Body of the message (An HTML version and a plain-text version).
# Read HTML from file
with codecs.open('regular_metting_email.html', mode='r', encoding='utf-8') as f:
    html = f.read()

# Fill variable data
next_meeting_date = next_weekday(datetime.date.today(), meeting_day)
date_string = u'{0}, {1}'.format(days_names[meeting_day], str(next_meeting_date.strftime("%d/%m")))
html = html.replace('#date', date_string)

# Strip html to create a plain-text version
strip_html_expr = re.compile('<.*?>')
text = re.sub(strip_html_expr, '', html)

# Record the MIME types of both parts - text/plain and text/html.
part1 = MIMEText(text, 'plain')
part2 = MIMEText(html, 'html')

# Attach parts into message container.
# According to RFC 2046, the last part of a multipart message, in this case
# the HTML message, is best and preferred.
msg.attach(part1)
msg.attach(part2)

# Send the message via local SMTP server.
s = smtplib.SMTP('localhost')
# sendmail function takes 3 arguments: sender's address, recipient's address
# and message to send - here it is sent as one string.
s.sendmail(sender, recepient, msg.as_string())
s.quit()

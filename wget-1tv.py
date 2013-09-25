#!/usr/bin/env python
# coding: utf-8

"""wget wrapper for downloading 1TV channel news

Usage:
    wget-1tv.py last
    wget-1tv.py list
    wget-1tv.py <PLAYLIST_URL>
    wget-1tv.py (-h | --help)

Options:
  -h, --help  show this help message and exit
  last        download last news release
  list        list available news releases

"""

import re
import datetime
import itertools
import subprocess

import times
import requests
from docopt import docopt
from lxml import etree
from pytils.dt import ru_strftime


MAIN_URL = 'http://www.1tv.ru'
NEWS_ARCHIVE_LINK = 'http://www.1tv.ru/newsvideoarchive/'
VIDEO_LINK_RE = re.compile(r'http://www-download\.1tv\.ru/\S+\.mp4')
PLAYLIST_LINK_XPATH = '//iframe[@name="video_play"]/@src'


def download_news(link_to_playlist=None):
    if link_to_playlist is None:
        print 'Fetching %s...' % MAIN_URL

        r = requests.get(MAIN_URL)
        et = etree.HTML(r.text)
        link_to_playlist = et.xpath(PLAYLIST_LINK_XPATH)[0]

        print 'Link to last news playlist: %s' % link_to_playlist

    print 'Fetching %s...' % link_to_playlist

    r = requests.get(link_to_playlist)
    video_links = VIDEO_LINK_RE.findall(r.text)

    print 'Call wget...'
    return subprocess.call(['wget', '-c'] + video_links)


def get_news():
    print 'Fetching %s...' % NEWS_ARCHIVE_LINK

    r = requests.get(NEWS_ARCHIVE_LINK)
    et = etree.HTML(r.text)
    blocks = et.xpath('//div[@class="n_day-video"]/ul/li/div[@class="low"]')

    news = []

    for block in blocks:
        name = block.xpath('div[@class="video_txt"]/a/text()')[0]
        link = block.xpath('a/@href')[0]

        _, date, number = link.rsplit('/', 2)

        number = int(number)

        date = date.split('.')
        date = map(int, date)
        date = reversed(date)
        date = datetime.date(*date)

        date_ru = ru_strftime(format=u'%d %B %Y', date=date, inflected=True)

        news.append({
            'link': link,
            'name': name,
            'date': date,
            'date_ru': date_ru,
            'number': number,
        })

    news.sort(key=lambda new: (new['date'], new['number']))

    return news


def print_news(news):
    print
    by_date = lambda new: new['date_ru']
    for key, subiter in itertools.groupby(news, by_date):
        print key
        for new in subiter:
            print u'    {0} — {1}'.format(new['name'], new['link'])
        print


if __name__ == '__main__':
    arguments = docopt(__doc__, version='wget-1tv 0.1')

    if arguments['list']:
        news = get_news()
        print_news(news)
    elif arguments['last']:
        download_news()
    else:
        download_news(arguments['<PLAYLIST_URL>'])

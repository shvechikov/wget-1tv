# coding: utf-8

"""
wget wrapper for downloading 1TV channel news

usage: wget-1tv.py [-h] (--last | --list | LINK)

positional arguments:
  LINK        a link to a playlist

optional arguments:
  -h, --help  show this help message and exit
  --last      download last news
  --list      list news

"""

import re
import sys
import operator
import datetime
import itertools
import subprocess

import times
import requests
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
    import argparse
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--last', action='store_true', help='download last news')
    group.add_argument('--list', action='store_true', help='list news')
    group.add_argument('link', nargs='?', metavar='LINK', help='a link to a playlist')
    args = parser.parse_args()

    if args.list:
        news = get_news()
        print_news(news)
    elif args.link:
        download_news(args.link)
    else:
        download_news()

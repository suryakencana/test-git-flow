"""
 # Copyright (c) 09 2015 | surya
 # 02/09/15 nanang.ask@kubuskotak.com
 # This program is free software; you can redistribute it and/or
 # modify it under the terms of the GNU General Public License
 # as published by the Free Software Foundation; either version 2
 # of the License, or (at your option) any later version.
 #
 # This program is distributed in the hope that it will be useful,
 # but WITHOUT ANY WARRANTY; without even the implied warranty of
 # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 # GNU General Public License for more details.
 #
 # You should have received a copy of the GNU General Public License
 # along with this program; if not, write to the Free Software
 # Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 #  mangaeden.py
"""
from datetime import datetime, timedelta
import logging
import time
import shutil

from concurrent.futures import ThreadPoolExecutor
from niimanga.libs.exceptions import HtmlError
from niimanga.models.master import ISOLang
from os import path, makedirs
from niimanga.libs import utils
from niimanga.models.manga import Manga, Chapter
from .celery import load_ini
from niimanga.models.meta.base import initialize_sql, DBSession
import re
import requests
from requests.packages.urllib3.connection import ConnectionError
from requests_futures.sessions import FuturesSession
import transaction

LOG = logging

INI = load_ini()
initialize_sql(INI)


def _chapter_slug(str_, slug_manga):
    name = str_
    # print(name[name.index("C"):])
    no = re.search(r"\d+(\.\d+)?", name[name.index("C"):]).group(0)
    # print(no)
    return no, utils.slugist('{1}-chapter-{0}'.format(no.zfill(3), slug_manga))


def build_to_sys(site, source):
    try:
        url = source.get('last_url')
        # print(url)
        resp_content = site.get_html(url)
        series_info = site.series_info(resp_content)

        # series == manga
        qry = Manga.query
        manga = qry.filter(Manga.slug == utils.slugist(
            "-".join([site.netlocs[4], series_info.get('name', None)])
        )).first()
        if manga is None:
            with transaction.manager:
                manga = Manga(
                    site.netlocs[4],
                    utils.HTMLUnscaped(series_info.get('name', u'')),
                    0,
                    ", ".join(series_info.get('tags', [])),
                    series_info.get('authors', u''),
                    series_info.get('artists', u''),
                    utils.HTMLUnscaped(series_info.get('aka', u'')),
                    utils.HTMLUnscaped(series_info.get('description', u'')),
                    1 if 'ongoing' in series_info.get('status', '').lower()
                    else 2 if 'completed' in series_info.get('status', '').lower() else 0
                )
                # manga.id = utils.guid()
                manga.origin = source.get('origin', '')
                manga.chapter_updated = datetime.fromtimestamp(source.get('time', 'now'))
                ext = series_info.get('thumb_url', '').lower().rsplit('.', 1)[-1]
                manga.thumb = '.'.join(['cover', ext])
                manga.category = 'ja'
                DBSession.add(manga)
                DBSession.flush()

        manga = qry.filter(Manga.slug == utils.slugist(
            "-".join([site.netlocs[4], series_info.get('name', None)])
        )).first()
        manga_id, manga_thumb, manga_slug = manga.id, manga.thumb, manga.slug
        ini_path = path.join(
            path.dirname(
                path.dirname(__file__)
            ),
            '/'.join(['rak', 'manga', manga_id])
        )

        r = requests.get(series_info.get('thumb_url', ''))
        path_img = '/'.join([ini_path, manga_thumb])
        print(path_img)
        if not path.exists(ini_path):
            makedirs(ini_path)
        with open(path_img, "wb") as code:
            code.write(r.content)

        chapters_info = series_info.get('chapters', [])
        for i, ch in enumerate(chapters_info):
            print(ch.get('name', ''))
            ch_name = str(ch.get('order', 0)) if ch.get('name', '') is None else utils.HTMLUnscaped(ch.get('name', u''))
            # edenapi slug
            slug_bt = ch_name

            # if ':' in slug_bt:
            #     slug_bt = slug_bt.split(':')
            #     slug_bt.pop(0)
            #     slug_bt = '-'.join(slug_bt)

            slug_chapter = ' '.join([manga_slug, slug_bt])
            # cek chapter sudah didownload
            chapter = Chapter.query.filter(Chapter.slug == utils.slugist(slug_chapter)).first()
            if chapter is None:

                v = utils.parse_number(ch_name, "Vol")
                v = 0 if v is None else v
                c = ch.get('order', 0)

                with transaction.manager:
                    chapter = Chapter(
                        slug_bt,
                        c,
                        v
                    )
                    time = datetime.fromtimestamp(ch.get('time', datetime.now()))
                    # chapter.id = utils.guid()
                    ch_manga = Manga.query.get(manga_id)
                    ch_manga.chapter_count += 1
                    chapter.lang = ISOLang.query.filter(ISOLang.iso == 'en').first()
                    chapter.updated = time
                    chapter.manga = ch_manga
                    # s = 1000v + c
                    # chapter.sortorder = (1000*float(v)) + float(c)
                    chapter.sortorder = float(c)
                    chapter.slug = slug_chapter
                    DBSession.add(chapter)
                    DBSession.flush()

                chapter = Chapter.query.filter(Chapter.slug == utils.slugist(slug_chapter)).first()

                # eden
                headers = {'content-type': 'application/json; charset=utf8'}
                html = site.get_html(ch.get('url'), headers=headers)
                # # ambil image dan download locally di folder chapter.id
                chapter_info = site.chapter_info(html)
                try:
                    # series info
                    # chapter info and images
                    session = FuturesSession(executor=ThreadPoolExecutor(max_workers=10))

                    for n, page in enumerate(chapter_info.get('pages', [])):
                        ini_chapter = '/'.join([ini_path, chapter.id])
                        print(page)
                        r = session.get(page).result()
                        if r.status_code != 200:
                            raise HtmlError('cannot fetch')
                        # path_img = '/'.join([ini_chapter, page.split('/')[-1]])
                        ext = page.split('/')[-1].rsplit('.', 1)[-1]
                        path_img = '/'.join([ini_chapter, "{num:03d}.{ext}".format(num=n, ext=ext)])
                        print(path_img)
                        if not path.exists(ini_chapter):
                            makedirs(ini_chapter)
                        with open(path_img, "wb") as code:
                            code.write(r.content)
                except ConnectionError as Conn:
                    print(Conn)
                    chapter = Chapter.query.get(chapter.id)
                    DBSession.delete(chapter)
                    shutil.rmtree(ini_chapter)

    except AttributeError as e:
        print(e.message)
    except KeyError as e:
        print(e.message)
    except ValueError as e:
        print(e.message)


def _parse_update_date(updatedate):
    if 'Today' in updatedate:
        diff = 0
        delta = str(updatedate).replace('Today', '')
    elif 'Yesterday' in updatedate:
        diff = -(1 * 86400)
        delta = str(updatedate).replace('Yesterday', '')
    else:
        return time.mktime(datetime.strptime(updatedate.strip(), "%b %d, %Y").timetuple())

    return time.mktime((datetime.strptime("{:%d-%m-%Y} {}".format(datetime.now(),
                                                                  delta.strip()), "%d-%m-%Y %I:%M %p")
                        + timedelta(seconds=diff)).timetuple())

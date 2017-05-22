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
 #  mangaedenapi.py
"""
import logging
import urllib
from datetime import timedelta, datetime
import time
import shutil

from concurrent.futures import ThreadPoolExecutor
from niimanga.models.master import ISOLang
from os import path, makedirs
from bs4 import BeautifulSoup
from niimanga.ctasks.celery import load_ini
from niimanga.libs import utils
from niimanga.models.manga import Manga, Chapter
from niimanga.models.meta.base import initialize_sql, DBSession
from niimanga.sites import Site
import requests
from requests.packages.urllib3.connection import ConnectionError
from requests_futures.sessions import FuturesSession
import transaction
from PIL import Image

LOG = logging.getLogger(__name__)

INI = load_ini()
initialize_sql(INI)


class MangaEdenApi(Site):
    netlocs = [
        u'www.mangaeden.com',
        u'mangaeden',
        u'https://www.mangaeden.com',
        u'http://cdn.mangaeden.com/mangasimg/',
        u'ed'
    ]

    def search_latest(self, keyword=None):
        url = self.netlocs[2] + '/ajax/news/1/0/'
        resp = requests.get(url)

        search_results = []
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.content, "html.parser")

        try:
            en_rows = soup.find_all('li')

            for i, rows in enumerate(en_rows):
                origin_url = rows.find('div', class_='newsManga').attrs['id']
                title = rows.find('div', class_='manga_tooltop_header').find('a', text=True).text.replace('\n', '')
                origin = rows.find('div', class_='manga_tooltop_header').find('a').attrs['href']
                time_element = rows.find('div', class_='chapterDate').text.replace('\n', '')

                search_results.append(
                    dict(
                        thumb=None,
                        origin=u'{url}{origin}'.format(url=self.netlocs[2], origin=origin),
                        name=title,
                        time=self._parse_update_date(time_element),
                        last_chapter=None,
                        last_url="{url}/api/manga/{id}/".format(url=self.netlocs[2], id=origin_url[:24]),
                        site=self.netlocs[1]
                    )
                )

            return search_results
        except AttributeError as e:
            print(e.message)
            return []

    def _parse_update_date(self, updatedate):
        if 'Today' in updatedate:
            diff = 0
            delta = str(updatedate).replace('Today', '')
        elif 'Yesterday' in updatedate:
            diff = -(1 * 86400)
            delta = str(updatedate).replace('Yesterday', '')
        else:
            return time.mktime(datetime.strptime(updatedate.strip(), "%b %d, %Y").timetuple())

        return time.mktime((datetime.strptime("{:%d-%m-%Y} {}"
                                              .format(datetime.now(), delta.strip()),
                                              "%d-%m-%Y %I:%M %p") + timedelta(seconds=diff)).timetuple())

    def search_by_author(self, author):
        url = self.netlocs[2] + '/en-directory/?author=' + urllib.quote(author)
        resp = requests.get(url)

        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.content, "html.parser")

        try:
            table = soup.find('table', id='mangaList')
            rows = table.find_all('tr', class_='')
            hrefs = [tr.find('td').find('a')
                     for tr in rows if 'style' not in tr.attrs]

            return [
                {
                    'name': a.text.strip(),
                    'url': a['href'],
                    'site': self.netlocs[1]
                } for a in hrefs
                ]

        except Exception:
            return []

    def _chapters(self, obj):
        try:
            chapters = []
            for row in obj['chapters']:
                chapters.append({
                    'order': row[0],
                    'name': row[2],
                    'url': u'{url}/api/chapter/{id}'.format(url=self.netlocs[2], id=row[3]),
                    'time': row[1]
                })
            return chapters

        except AttributeError:
            return []

    def _thumbnail_url_and_tags(self, jsoup):
        try:
            img = jsoup["image"] if jsoup["image"] is not None else jsoup["imageURL"]
            thumb = "{url}/{img}".format(url=self.netlocs[3], img=img)
            tags = jsoup["categories"]
            print(img)

            return thumb, tags
        except AttributeError:
            return [], []

    def _name(self, jsoup):
        return utils.HTMLUnscaped(jsoup['title'])

    def _alias(self, jsoup):
        return ', '.join([utils.HTMLUnscaped(aka) for aka in jsoup['aka']])

    def _status(self, jsoup):
        status = jsoup['status']
        return u'completed' if status == 1 else u'ongoing'

    def _authors(self, jsoup):
        return jsoup['author'].lower()

    def _artists(self, jsoup):
        return jsoup['artist'].lower()

    def _description(self, jsoup):
        return utils.HTMLUnscaped(jsoup['description'])

    def series_info(self, jsonUnparsed):

        jsoup = utils.loads(jsonUnparsed)
        chapters = self._chapters(jsoup)
        thumb_url, tags = self._thumbnail_url_and_tags(jsoup)
        name = self._name(jsoup)
        aka = self._alias(jsoup)
        status = self._status(jsoup)
        description = self._description(jsoup)
        authors = self._authors(jsoup)
        artists = self._artists(jsoup)

        return {
            'chapters': chapters,
            'thumb_url': thumb_url,
            'name': name,
            'aka': aka,
            'tags': tags,
            'status': status,
            'description': description,
            'authors': authors,
            'artists': artists,
            'site': self.netlocs[1]
        }

    def chapter_info(self, jsoup, **kwargs):

        jsoup = utils.loads(jsoup)

        pages = self._chapter_pages(jsoup['images'])
        # name = self._chapter_name(soup)
        # series_url = self._chapter_series_url(soup)
        # prev, next = self._chapter_prev_next(soup)
        return {
            'name': None,
            'pages': pages,
            'series_url': None,
            'next_chapter_url': None,
            'prev_chapter_url': None,
        }

    def _chapter_pages(self, images):
        # list images
        """
            [
              23,
              "5c/5c8bf44d054c167b08dea5265e1f18cc9fa7996f268bbd7e5be46bc7.jpg",
              869,
              1249
            ],
        """
        returns = []
        for image in images:
            urls = image[1]
            order = image[0]
            returns.append(u'{url}{image}'.format(url=self.netlocs[3], image=urls))
        returns.reverse()
        return returns

    def build_to_sys(self, site, source):
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
                ch_name = str(ch.get('order', 0)) if ch.get('name', '') is None else utils.HTMLUnscaped(
                    ch.get('name', u''))
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
                                # raise HtmlError('cannot fetch')
                                continue
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

    def script_to_sys(self, source_url, source_origin, time_str):
        """
        untuk url API mangaeden + id manga[:24]
        python scripts/mangascrapper.py -s https://www.mangaeden.com/api/manga/4e70ea1dc092255ef7004d5c/ -o http://www.mangaeden.com/en/en-manga/fairy-tail/ -t "Aug 31, 2015"

        :param self: Manga API
        :param source_url: url data manga untuk di scrap
        :param source_origin: url sumber manga
        :param time: chapter release terakhir Agust 30, 2015(string time)
        : fairy tail https://www.mangaeden.com/api/manga/4e70ea1dc092255ef7004d5c/
        : naruto http://www.mangaeden.com/api/manga/4e70ea03c092255ef70046f0/
        : one piece http://www.mangaeden.com/api/manga/4e70ea10c092255ef7004aa2/
        : bleach http://www.mangaeden.com/api/manga/4e70e9efc092255ef7004274/
        : nanatsu http://www.mangaeden.com/api/manga/5099a865c092254a2000daf4/
        :return:
        """
        try:
            # print(url)
            # "{url}/api/manga/{id}/".format(url=self.netlocs[2], id=origin_url[:24])
            # https://www.mangaeden.com/api/manga/:id[:24]/
            resp_content = self.get_html(source_url)
            series_info = self.series_info(resp_content)
            time_long = self._parse_update_date(time_str) if isinstance(time_str, basestring) else long(time_str)
            # series == manga
            qry = Manga.query
            manga = qry.filter(Manga.slug == utils.slugist(
                "-".join([self.netlocs[4], series_info.get('name', None)])
            )).first()
            if manga is None:
                with transaction.manager:
                    manga = Manga(
                        self.netlocs[4],
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
                    manga.origin = source_origin
                    manga.chapter_updated = datetime.fromtimestamp(time_long)
                    ext = series_info.get('thumb_url', '').lower().split('.')[-1]
                    manga.thumb = '.'.join(['cover', ext])
                    manga.category = 'ja'
                    DBSession.add(manga)
                    DBSession.flush()

            manga = qry.filter(Manga.slug == utils.slugist(
                "-".join([self.netlocs[4], series_info.get('name', None)])
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
                ch_name = str(ch.get('order', 0)) if ch.get('name', '') is None else utils.HTMLUnscaped(
                    ch.get('name', u''))
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
                    html = self.get_html(ch.get('url'), headers=headers)
                    # # ambil image dan download locally di folder chapter.id
                    chapter_info = self.chapter_info(html)
                    try:
                        # series info
                        # chapter info and images
                        session = FuturesSession(executor=ThreadPoolExecutor(max_workers=10))

                        for n, page in enumerate(chapter_info.get('pages', [])):
                            ini_chapter = '/'.join([ini_path, chapter.id])
                            print(page)
                            r = session.get(page).result()
                            if r.status_code != 200:
                                print('continue chapter')
                                continue
                                # raise HtmlError('cannot fetch')
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

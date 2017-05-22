import logging
import urllib
import shutil
from concurrent.futures import ThreadPoolExecutor
from niimanga.models.master import ISOLang
from os import path, makedirs
from niimanga.ctasks.celery import load_ini
from niimanga.libs import utils

from niimanga.libs.utils import LocalDateTime
from niimanga.models.manga import Manga, Chapter
from niimanga.models.meta.base import initialize_sql, DBSession
import re
from niimanga.sites import Site
from niimanga.libs.exceptions import HtmlError
import requests
import bs4
from bs4 import BeautifulSoup
from requests.packages.urllib3.connection import ConnectionError
from requests_futures.sessions import FuturesSession
import transaction

LOG = logging.getLogger(__name__)

INI = load_ini()
initialize_sql(INI)
# Define custom BeautifulSoup filter to get <img> tags that are sure to hold
# manga page image url


def _page_img_tag(tag):
    if tag.name == 'img' and 'src' in tag.attrs:
        _page_url_pat = re.compile('^http://img.bato.to/comics/\d{4}.*$')
        return bool(_page_url_pat.match(tag.attrs['src']))
    return False


class Batoto(Site):
    parseDate = LocalDateTime.now()
    # tag url | site name | url path | url image
    netlocs = ['bato.to', 'batoto', 'http://bato.to', 'http://img.bato.to/forums/uploads/', 'bt']

    def prime_loop(self, num):
        if num > 1:
            # check for factors
            for i in range(2, num):
                if (num % i) == 0:
                    # print(num, "is not a prime number")
                    # print(i, "times", num//i, "is", num)
                    return False
            else:
                return True
        return False

    def search_latest(self, keyword=None):
        url = self.netlocs[2]
        resp = requests.get(url)

        search_results = []
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.content)

        try:
            table = soup.find('table', class_='chapters_list')
            en_rows = table.find_all('tr', class_='lang_English')
            # print(len(en_rows))
            for i, rows in enumerate(en_rows):
                if rows.find('a', style='font-weight:bold;') is not None:
                    image_thumb = rows.find('img').attrs['src']
                    origin_url = rows.find_all('a')[-1].attrs['href']
                    title = rows.find_all('a')[-1].text

                    child = en_rows[i + 1]
                    last_title = child.find('a').text
                    last_url = child.find('a').attrs['href']
                    time = child.find_all('td')[-1].text
                    search_results.append(
                        dict(
                            thumb=self.netlocs[3] + image_thumb.split('/')[-1],
                            origin=origin_url,
                            name=title,
                            time=self.parseDate.human_to_date_stamp(time),
                            last_chapter=last_title,
                            last_url=last_url,
                            site=self.netlocs[1]
                        )
                    )
            return search_results
        except AttributeError as e:
            print(e)
            return []

    def search_popular(self, keyword=None):
        url = self.netlocs[2]
        resp = requests.get(url)

        search_results = []
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.content)

        try:
            table = soup.find('ul', class_='block_list')
            en_rows = table.find_all('li', class_='hentry')
            # print(len(en_rows))
            for i, rows in enumerate(en_rows):
                # if rows.find('a', style='font-weight:bold;') is not None:
                image_thumb = rows.find('img').attrs['src']
                origin_url = rows.find('a').attrs['href']
                title = rows.find('img').attrs['alt']

                last_title = rows.find_all('a')[-1].text
                last_url = rows.find_all('a')[-1].attrs['href']

                search_results.append(
                    dict(
                        thumb=self.netlocs[3] + image_thumb.split('/')[-1],
                        origin=origin_url,
                        name=title,
                        time=self.parseDate.to_time_stamp(self.parseDate.timetuple()),
                        last_chapter=last_title,
                        last_url=last_url,
                        site=self.netlocs[1]
                    )
                )
            return search_results
        except AttributeError as e:
            print(e)
            return []

    def _normalize_series_url(self, url):
        """
        Series URLs from search results are in this form:
            http://bato.to/comic/_/beelzebub-r4
        while in other places the URL is
            http://bato.to/comic/_/comics/beelzebub-r4

        This function transforms the first form into the second for
        consistency, otherwise url-based features like chapter progresses won't
        work properly.
        """
        parts = url.split('/')
        if len(parts) == 6 and parts[:5] == ['http:', '', 'bato.to', 'comic',
                                             '_']:
            parts.insert(5, 'comics')
            return '/'.join(parts)
        return url

    def search_series(self, keyword):
        url = self.netlocs[2] + '/search?'
        params = {
            'name_cond': 'c',  # "name contains keyword"
            'name': keyword
        }

        # url += urllib.urlencode(params)
        resp = requests.get(url, params)

        if resp.status_code != 200:
            return []  # TODO maybe show some meaningful error alert to user?

        soup = BeautifulSoup(resp.content)
        table = soup.find('table', class_='chapters_list')
        strongs = table.find_all('strong')
        series_list = []
        for strong in strongs:
            a = strong.find('a')
            url = a['href']
            name = a.contents[1].strip()
            series_list.append({
                'url': self._normalize_series_url(url),
                'name': name,
                'site': self.netlocs[1],
            })
        return series_list

    def series_info(self, html):
        soup = BeautifulSoup(html)
        chapters = self._chapters(soup)
        thumb_url, tags = self._thumbnail_url_and_tags(soup)
        name = self._name(soup)
        status = self._status(soup)
        description = self._description(soup)
        authors = self._authors(soup)
        artists = self._artists(soup)
        aka = self._aka(soup)

        return {
            'chapters': chapters,
            'thumb_url': thumb_url,
            'name': name,
            'tags': tags,
            'status': status,
            'description': description,
            'authors': authors,
            'artists': artists,
            'aka': aka,
            'site': self.netlocs[1],
        }

    def _name(self, soup):
        return utils.HTMLUnscaped(soup.find('h1', class_='ipsType_pagetitle').contents[0].strip())

    def _chapters(self, soup):
        try:
            table = soup.find('table', class_='chapters_list')
            en_rows = table.find_all('tr', class_='lang_English')

            chapters = []
            for row in en_rows:
                a = row.find('a')
                url = a['href']
                name = a.contents[1].strip()
                time = row.find_all('td')[-1].text.strip()
                chapters.append({
                    'name': name,
                    'url': url,
                    'time': time
                })
            return chapters

        except AttributeError:
            return []

    def _thumbnail_url_and_tags(self, soup):
        try:
            box = soup.find('div', class_='ipsBox')
            thumb = box.find('img')['src']

            # This cell stores <a> that store tags
            tags_cell = box.find('td', text='Genres:').find_next_sibling('td')
            tags = [a.find('span').contents[1].strip().lower()
                    for a in tags_cell]
            return thumb, tags
        except AttributeError:
            return [], []

    def _status(self, soup):
        siblings = soup.find('td', text='Status:').next_siblings
        for s in siblings:
            if type(s) == bs4.element.Tag:
                return s.text.strip().lower()
        return 'unknown'

    def _description(self, soup):
        siblings = soup.find('td', text='Description:').next_siblings
        for s in siblings:
            if type(s) == bs4.element.Tag:
                # Batoto stuffs the whole description inside 1 single <p> tag,
                # using <br/> for line breaks. BeautifulSoup's get_text()
                # ignores those br tags by default, but get_text('separator')
                # replaces them with the provided separator, so we can split
                # the result using that same separator and have a proper list
                # of paragraphs.  Neat eh?
                return utils.HTMLUnscaped(s.get_text('|||').split('|||'))
        return ['unknown']

    def _authors(self, soup):
        authors = soup.find('td', text='Author:').next_siblings
        results = []
        # XXX: 3 nested loops. Yikes!
        # Should probably sprinkle some comprehensions on top?
        for sibling in authors:
            if type(sibling) == bs4.element.Tag and sibling.name == 'td':
                a_tags = sibling.find_all('a')
                for tag in a_tags:
                    name = tag.text.strip()
                    if name not in results:
                        results.append(name)
        return results

    def _artists(self, soup):
        artists = soup.find('td', text='Artist:').next_siblings
        results = []
        for sibling in artists:
            if type(sibling) == bs4.element.Tag and sibling.name == 'td':
                a_tags = sibling.find_all('a')
                for tag in a_tags:
                    name = tag.text.strip()
                    if name not in results:
                        results.append(name)
        return results

    def _aka(self, soup):
        aka = soup.find('td', text='Alt Names:').next_siblings
        results = []
        for sibling in aka:
            if type(sibling) == bs4.element.Tag and sibling.name == 'td':
                span_tags = sibling.find_all('span')
                for tag in span_tags:
                    name = utils.HTMLUnscaped(tag.text.strip())
                    if name not in results:
                        results.append(name)
        return results

    def chapter_info(self, html, **kwargs):
        soup = BeautifulSoup(html)
        pages = self._chapter_pages(soup, html)
        name = self._chapter_name(soup)
        series_url = self._chapter_series_url(soup)
        prev, next = self._chapter_prev_next(soup)
        return {
            'name': name,
            'pages': pages,
            'series_url': series_url,
            'next_chapter_url': next,
            'prev_chapter_url': prev,
        }

    def _chapter_prev_next(self, soup):
        next = soup.find('img', title='Next Chapter')
        if next is not None:
            next = next.parent['href']
        prev = soup.find('img', title='Previous Chapter')
        if prev is not None:
            prev = prev.parent['href']
        return prev, next

    def _chapter_name(self, soup):
        select = soup.find('select', attrs={'name': 'chapter_select'})
        return utils.HTMLUnscaped(select.find('option', selected=True).text.strip())

    def _chapter_series_url(self, soup):
        a_tag = soup.find('div', class_='moderation_bar').find('a')
        return a_tag['href']

    def _chapter_pages(self, soup, html):
        # For webtoons, all pages are shown in a single page.
        # When that's the case, there's this element that asks if you want to
        # view page-by-page instead. Let's use this element to check if we're
        # parsing a webtoon chapter.
        webtoon = soup.find('a', href='?supress_webtoon=t')
        if webtoon is not None:
            img_tags = soup.find_all(_page_img_tag)
            return [
                tag['src']
                for tag in img_tags
                ]

        # a <select> tag has options that each points to a page
        opts = soup.find('select', id='page_select').find_all('option')
        urls = [opt['value'] for opt in opts]

        # Page 1 has already been fetched (stored in this html param, duh!)
        # so let's save ourselves an http request
        pages_htmls = [html]
        urls = urls[1:]
        session = FuturesSession()

        for order, url in enumerate(urls):
            res = session.get(url).result()
            if res.status_code != 200:
                raise HtmlError('cannot fetch')
            pages_htmls.append(res.content)

        returns = []
        for page_html in pages_htmls:
            soup = BeautifulSoup(page_html)
            img_url = soup.find('img', id='comic_page')['src']
            returns.append(img_url)
        return returns

    def search_by_author(self, author):
        url = self.netlocs[2] + '/search?artist_name=' + urllib.quote(author)
        resp = requests.get(url)

        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.content)

        try:
            table = soup.find('table', class_='chapters_list')
            rows = table.find_all('tr', class_='')
            hrefs = [tr.find('td').find('strong').find('a')
                     for tr in rows if 'style' not in tr.attrs]

            return [
                {
                    'name': a.text.strip(),
                    'url': a['href'],
                    'site': self.netlocs[1],
                } for a in hrefs
                ]

        except AttributeError:
            return []

    def build_to_sys(self, site, source):
        try:
            lt = LocalDateTime.now()
            """
                dict(
                    thumb=self.netlocs[3] + "/".join([image_thumb.split('/')[-2], image_thumb.split('/')[-1]]),
                    origin=origin_url,
                    name=title,
                    # time=self.parseDate.human_to_date_stamp(time),
                    time=time,
                    last_chapter=last_title,
                    last_url=last_url,
                    site=self.netlocs[1]
                )
            """
            # list latest
            # scrap series info
            # url = "/".join([site.netlocs[2], source.get('origin')])
            url = source.get('origin')
            # print(url)
            respcontent = site.get_html(url)
            series_info = site.series_info(respcontent)

            # series == manga
            qry = Manga.query
            manga = qry.filter(Manga.slug == utils.slugist(
                "-".join([site.netlocs[4], source.get('name', None)])
            )).first()
            if manga is None:
                with transaction.manager:
                    manga = Manga(
                        site.netlocs[4],
                        series_info.get('name', []),
                        0,
                        ", ".join(series_info.get('tags', [])),
                        ", ".join(series_info.get('authors', [])),
                        ", ".join(series_info.get('artists', [])),
                        ', '.join(series_info.get('aka', [])),
                        ",".join(series_info.get('description', None)),
                        1 if 'ongoing' in series_info.get('status', '').lower()
                        else 2 if 'completed' in series_info.get('status', '').lower() else 0
                    )
                    # manga.id = utils.guid()
                    manga.origin = source.get('origin', '')
                    manga.chapter_updated = lt.from_time_stamp(source.get('time', 'now'))
                    ext = series_info.get('thumb_url', '').lower().rsplit('.', 1)[-1]
                    manga.thumb = '.'.join(['cover', ext])
                    manga.category = 'ja'
                    DBSession.add(manga)
                    DBSession.flush()

            manga = qry.filter(Manga.slug == utils.slugist(
                "-".join([site.netlocs[4], source.get('name', None)])
            )).first()
            manga_id, manga_thumb, manga_slug = manga.id, manga.thumb, manga.slug
            ini_path = path.join(
                path.dirname(
                    path.dirname(__file__)
                ),
                '/'.join(['rak', 'manga', manga_id])
            )

            r = requests.get(source.get('thumb'))
            path_img = '/'.join([ini_path, manga_thumb])
            print(path_img)
            if not path.exists(ini_path):
                makedirs(ini_path)
            with open(path_img, "wb") as code:
                code.write(r.content)

            chapters_info = series_info.get('chapters', [])
            for i, ch in enumerate(chapters_info):
                print(ch.get('name', ''))
                # batoto slug
                slug_bt = ch.get('name', '')

                if ':' in slug_bt:
                    slug_bt = slug_bt.split(':')
                    slug_bt.pop(0)
                    slug_bt = '-'.join(slug_bt)

                slug_chapter = ' '.join([manga_slug, slug_bt])
                # cek chapter sudah didownload
                chapter = Chapter.query.filter(Chapter.slug == utils.slugist(slug_chapter)).first()
                if chapter is None:

                    v = utils.parse_number(ch.get('name', ''), "Vol")
                    v = 0 if v is None else v
                    c = utils.parse_number(ch.get('name', ''), "Ch")
                    c = 0 if c is None else c

                    with transaction.manager:
                        chapter = Chapter(
                            slug_bt,
                            c,
                            v
                        )
                        time = lt.human_to_date(ch.get('time', 'now'))
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

                    # batoto
                    html = site.get_html(ch.get('url'))
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
                            ext = page.split('/')[-1].rsplit('.', 1)[-1]
                            path_img = '/'.join([ini_chapter, "{num:03d}.{ext}".format(num=n, ext=ext)])
                            # path_img = '/'.join([ini_chapter, page.split('/')[-1]])
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

    def script_to_sys(self, source, time_local=None):
        try:
            lt = LocalDateTime.now()
            """
                dict(
                    thumb=self.netlocs[3] + "/".join([image_thumb.split('/')[-2], image_thumb.split('/')[-1]]),
                    origin=origin_url,
                    name=title,
                    # time=self.parseDate.human_to_date_stamp(time),
                    time=time,
                    last_chapter=last_title,
                    last_url=last_url,
                    site=self.netlocs[1]
                )
            """
            # list latest
            # scrap series info
            # url = "/".join([site.netlocs[2], source.get('origin')])
            url = source
            # print(url)
            respcontent = self.get_html(url)
            series_info = self.series_info(respcontent)

            # series == manga
            qry = Manga.query
            manga = qry.filter(Manga.slug == utils.slugist(
                "-".join([self.netlocs[4], series_info.get('name', [])])
            )).first()
            if manga is None:
                with transaction.manager:
                    manga = Manga(
                        self.netlocs[4],
                        series_info.get('name', []),
                        0,
                        ", ".join(series_info.get('tags', [])),
                        ", ".join(series_info.get('authors', [])),
                        ", ".join(series_info.get('artists', [])),
                        ', '.join(series_info.get('aka', [])),
                        ",".join(series_info.get('description', None)),
                        1 if 'ongoing' in series_info.get('status', '').lower()
                        else 2 if 'completed' in series_info.get('status', '').lower() else 0
                    )
                    # manga.id = utils.guid()
                    manga.origin = url
                    manga.chapter_updated = lt.from_time_stamp(time_local)
                    ext = series_info.get('thumb_url', '').lower().rsplit('.', 1)[-1]
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

            r = requests.get(series_info.get('thumb_url'))
            path_img = '/'.join([ini_path, manga_thumb])
            print(path_img)
            if not path.exists(ini_path):
                makedirs(ini_path)
            with open(path_img, "wb") as code:
                code.write(r.content)

            chapters_info = series_info.get('chapters', [])
            for i, ch in enumerate(chapters_info):
                print(ch.get('name', ''))
                # batoto slug
                slug_bt = ch.get('name', '')

                if ':' in slug_bt:
                    slug_bt = slug_bt.split(':')
                    slug_bt.pop(0)
                    slug_bt = '-'.join(slug_bt)

                slug_chapter = ' '.join([manga_slug, slug_bt])
                # cek chapter sudah didownload
                chapter = Chapter.query.filter(Chapter.slug == utils.slugist(slug_chapter)).first()
                if chapter is None:

                    v = utils.parse_number(ch.get('name', ''), "Vol")
                    v = 0 if v is None else v
                    c = utils.parse_number(ch.get('name', ''), "Ch")
                    c = 0 if c is None else c

                    with transaction.manager:
                        chapter = Chapter(
                            slug_bt,
                            c,
                            v
                        )
                        time = lt.human_to_date(ch.get('time', 'now'))
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

                    # batoto
                    html = self.get_html(ch.get('url'))
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
                                # raise HtmlError('cannot fetch')
                                continue
                            ext = page.split('/')[-1].rsplit('.', 1)[-1]
                            path_img = '/'.join([ini_chapter, "{num:03d}.{ext}".format(num=n, ext=ext)])
                            # path_img = '/'.join([ini_chapter, page.split('/')[-1]])
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
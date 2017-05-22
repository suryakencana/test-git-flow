"""
 # Copyright (c) 04 2015 | surya
 # 21/04/15 nanang.ask@kubuskotak.com
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
 #  main.py
"""
import arrow
from dateutil import tz

from niimanga.configs.view import ZHandler
from niimanga.libs import utils
from niimanga.libs.crawlable import CrawlAble
from niimanga.libs.utils import slugist
from niimanga.models.manga import Manga, Chapter
from pyramid.view import view_config
from sqlalchemy import desc, and_, or_


class MainView(ZHandler):
    @staticmethod
    def _card_fill(_, cards):
        lt = arrow.utcnow()
        results = []
        for row in cards:
            past = arrow.get(row.chapter_updated.replace(tzinfo=tz.tzlocal()))
            time = past.humanize(lt)

            chapter = row.last_chapter(row.id)

            card = dict(
                origin='/'.join([row.slug]),
                name=row.title,
                time=time,
                last_chapter=' '.join(['Ch.', str(chapter.chapter).replace('.0', ''), chapter.title]),
                last_url='/'.join([row.slug, chapter.slug])
            )
            results.append(card)
        return results

    @view_config(route_name='home', renderer='layouts/home.html')
    @CrawlAble()
    def home_view(self):
        _ = self.R
        qry = Manga.query
        latest = qry \
            .filter(Manga.chapter_count > 0) \
            .order_by(desc(Manga.chapter_updated)) \
            .limit(50) \
            .all()
        return {'cards': MainView._card_fill(_, cards=latest)}

    @view_config(route_name='url_popular', renderer='layouts/popular.html')
    @CrawlAble()
    def popular_view(self):
        _ = self.R
        limit = int(_.params.get('cards', 100))
        offset = int(_.params.get('page', 0)) * limit
        qry = Manga.query
        popular = qry.filter(Manga.chapter_count > 0) \
            .order_by(desc(Manga.viewed)) \
            .offset(offset) \
            .limit(limit) \
            .all()
        return {'cards': MainView._card_fill(_, cards=popular)}

    @view_config(route_name='url_latest', renderer='layouts/latest.html')
    @CrawlAble()
    def latest_view(self):
        _ = self.R
        limit = int(_.params.get('cards', 100))
        offset = int(_.params.get('page', 0)) * limit
        qry = Manga.query

        latest = qry \
            .filter(Manga.chapter_count > 0) \
            .order_by(desc(Manga.chapter_updated)) \
            .offset(offset) \
            .limit(limit) \
            .all()
        return {'cards': MainView._card_fill(_, cards=latest)}

    @view_config(route_name='url_directories', renderer='layouts/directory.html')
    @CrawlAble()
    def directories_view(self):
        _ = self.R
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        non_alphabet = '1234567890.-+#$'
        q = _.matchdict.get('q', 0)
        qry = Manga.query
        try:
            q = int(q) if int(q) < 26 else -1
        except ValueError:
            q = -1

        if q < 0:
            directory = qry.filter(and_(or_(*[Manga.title.ilike(u'{q}%'.format(q=a)) for a in non_alphabet]),
                                        Manga.chapter_count > 0)) \
                .order_by(Manga.title) \
                .all()
        else:
            directory = qry.filter(and_(Manga.title.ilike(u'{q}%'.format(q=alphabet[q])), Manga.chapter_count > 0)) \
                .order_by(Manga.title) \
                .all()

        return {'cards': MainView._card_fill(_, cards=directory)}

    @view_config(route_name='url_series', renderer='layouts/series.html')
    @CrawlAble()
    def series_view(self):
        _ = self.R
        slug = _.matchdict.get('seriesSlug', "No Title")
        present = arrow.utcnow()
        qry = Manga.query
        manga = qry.filter(Manga.slug == slug.strip()).first()
        if manga is not None:
            filename = '/'.join([manga.id, manga.thumb])
            thumb = _.storage.url(filename)
            aka = utils.HTMLUnscaped(manga.aka)
            artists = utils.HTMLUnscaped(manga.get_artist())
            authors = utils.HTMLUnscaped(manga.get_authors())
            description = utils.HTMLUnscaped(manga.description)
            name = utils.HTMLUnscaped(manga.title)
            last = Manga.last_chapter(manga.id)
            time = manga.chapter_updated.strftime('%b %d, %Y')
            stags = manga.get_genre_tostr()
            tags = [dict(label=tag, value=slugist(tag)) for tag in stags.split(',')]

            results = []
            last_chapter = ''
            last_url = ''
            if last is not None:
                last_chapter = ' '.join([str(last.chapter), last.title])
                last_url = '/'.join([manga.slug, last.slug])

                manga.updated_viewed()
                chapters = Chapter.query.filter_by(tb_manga_id=manga.id).order_by(desc(Chapter.sortorder)).all()
                for chapter in chapters:
                    results.append(dict(
                        name=' '.join(['Ch.', str(chapter.chapter).replace('.0', ''), chapter.title]),
                        url='/'.join([manga.slug, chapter.slug, "0"]),
                        time=chapter.updated.strftime('%b %d, %Y')
                    ))

            return dict(
                aka=aka,
                url='/manga/{slug}'.format(slug=slug),
                thumb_url=thumb,
                artists=artists,
                authors=authors,
                description=description,
                name=name,
                tags=tags,
                time=time,
                last_chapter=last_chapter,
                last_url=last_url,
                chapters=results
            )
        return None

    @view_config(route_name='url_chapter', renderer='layouts/chapter.html')
    @CrawlAble()
    def chapter_view(self):
        _ = self.R
        slug = _.matchdict.get('seriesSlug', "No Title")
        chap_slug = _.matchdict.get('chapterSlug', "No Title")

        # cari manga by slug
        manga = Manga.query.filter(Manga.slug == slug).first()
        if manga is not None:
            filename = '/'.join([manga.id, manga.thumb])
            thumb = _.storage.url(filename)
            aka = utils.HTMLUnscaped(manga.aka)
            artists = utils.HTMLUnscaped(manga.get_artist())
            authors = utils.HTMLUnscaped(manga.get_authors())
            description = utils.HTMLUnscaped(manga.description)
            name = utils.HTMLUnscaped(manga.title)
            last = Manga.last_chapter(manga.id)
            last_chapter = ' '.join([str(last.chapter), last.title])
            # cari chapter manga
            chapter = manga.get_chapter(manga, chap_slug)
            ch = chapter.title if chapter.title == str(chapter.chapter) \
                .replace('.0', '') else '{ch} {chapter}' \
                .format(ch=str(chapter.chapter).replace('.0', ''), chapter=chapter.title)
            return dict(
                aka=aka,
                url='/chapter/{slug}/{chap}'.format(slug=slug, chap=chap_slug),
                thumb_url=thumb,
                artists=artists,
                authors=authors,
                description='Read newest {title} {ch} online'.format(
                    ch=ch,
                    title=manga.title
                ),
                name='{title} {ch}'.format(
                    ch=ch,
                    title=manga.title
                ),
                genres=manga.get_genre_tostr(),
                last_chapter=last_chapter,
                series_url=manga.slug
            )
        return {'project': 'moori'}

    @view_config(route_name='url_search', renderer='layouts/home.html')
    @CrawlAble()
    def search_view(self):

        return {'project': 'moori'}

    @view_config(route_name='url_genre', renderer='layouts/home.html')
    @CrawlAble()
    def genre_view(self):

        return {'project': 'moori'}

    @view_config(route_name='url_tags', renderer='layouts/home.html')
    @CrawlAble()
    def tags_view(self):

        return {'project': 'moori'}

    @view_config(context='pyramid.exceptions.NotFound', renderer='layouts/404.html')
    def not_found_view(self):
        return {'project': 'moori'}
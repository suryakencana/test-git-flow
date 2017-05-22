"""
 # Copyright (c) 03 2015 | surya
 # 02/03/15 nanang.ask@kubuskotak.com
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
 #  api.py
"""
import logging

import arrow
from dateutil import tz
from niimanga.libs.goog import GoogleSearch, clean_html
from niimanga.libs.manga import MangaUtil
from niimanga.models.manga import Chapter, Manga
from niimanga.models.master import Genre
from pyramid.view import view_config
from niimanga.libs.access import api_auth
from niimanga.libs.oauth.authorization import client_credentials_authorization
from niimanga.libs.oauth.request import RequestOAuth
from niimanga.libs.utils import ResponseHTTP, slugist
from niimanga.models.auth import UserMgr
from niimanga.configs.view import ZHandler
import requests
from sqlalchemy import desc, and_, not_, or_, func

LOG = logging.getLogger(__name__)


class ApiView(ZHandler):
    @view_config(route_name="api_ping", renderer="json")
    @api_auth('api_key', UserMgr.get)
    def ping(self):
        """Verify that you've setup your api correctly and verified

        """
        with ResponseHTTP(response=self.R.response) as t:
            i = [i for i in range(5000)]
            code, status = ResponseHTTP.INTERNAL_SERVER_ERROR
        return t.to_json(u'success', code=code, status=status, data={'ok': 'jamur'})

    @view_config(route_name="token_endpoint", renderer="json")
    def get_token(self):
        """Get Token dengan Api-key authz
            :GET ?grant_type=client_credentials&scope=member:basic
            Set Header
            :param Authorization i.e basic client_key:client_secret
            :param grant_type i.e [client_credentials, password, authorization_code]
        """
        request = RequestOAuth(self.R)

        with ResponseHTTP(request.response) as resp:
            grant_type = request.params.get('grant_type', None)
            _in = u'Failed'
            code, status = ResponseHTTP.NOT_AUTHORIZED
            message = 'authentication'
            if u'client_credentials' in grant_type:
                # optional scope
                scope = request.params.get('scope', 'member:basic')
                if scope:
                    scope = scope.split(' ')
                if request.authentication is not None:
                    LOG.debug('authentication')
                    return client_credentials_authorization(request.authentication, scope)
                LOG.debug('client_credentials')

            if u'authorization_code' in grant_type:
                code, status = ResponseHTTP.NOT_AUTHORIZED

            if u'password' in grant_type:
                code, status = ResponseHTTP.NOT_AUTHORIZED

        return resp.to_json(_in,
                            message=message,
                            code=code,
                            status=status)


class MangaApi(ZHandler):
    @staticmethod
    def _card_fill(_, cards):
        lt = arrow.utcnow()
        results = []
        for row in cards:
            past = arrow.get(row.chapter_updated.replace(tzinfo=tz.tzlocal()))
            time = past.humanize(lt)
            filename = '/'.join([row.id, row.thumb])
            thumb = _.storage.url(filename)
            chapter = row.last_chapter(row.id)
            # chapter = Chapter.query.first()
            card = dict(
                thumb='/{thumb}'.format(thumb=thumb),
                origin='/'.join([row.slug]),
                name=row.title,
                time=time,
                last_chapter=' '.join(['Ch.', str(chapter.chapter).replace('.0', ''), chapter.title]),
                last_url='/'.join([row.slug, chapter.slug, '0']),
                site='batoto' if 'bt' in row.type else 'mangaeden' if 'ed' in row.type else 'kk'
            )
            results.append(card)
        return results

    @view_config(route_name='latest_manga', renderer='json', request_method='POST')
    def latest_manga(self):
        _ = self.R
        limit = int(_.params.get('cards', 16))
        offset = int(_.params.get('page', 0)) * limit
        """ output
            dict(
            url = request.storage.url(filename)
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
        qry = Manga.query
        latest = qry \
            .filter(Manga.chapter_count > 0) \
            .order_by(desc(Manga.chapter_updated)) \
            .offset(offset) \
            .limit(limit) \
            .all()
        return MangaApi._card_fill(_, latest)

    @view_config(route_name='popular_manga', renderer='json')
    def popular_series(self):
        _ = self.R
        limit = int(_.params.get('cards', 0))
        offset = int(_.params.get('page', 0)) * limit
        qry = Manga.query
        popular = qry.filter(Manga.chapter_count > 0) \
            .order_by(desc(Manga.viewed)) \
            .offset(offset) \
            .limit(limit) \
            .all()
        return MangaApi._card_fill(_, popular)

    @view_config(route_name='directory_manga', renderer='json')
    def directory_series(self):
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
            LOG.debug(q)
            directory = qry.filter(and_(or_(*[Manga.title.ilike(u'{q}%'.format(q=a)) for a in non_alphabet]),
                                        Manga.chapter_count > 0)) \
                .order_by(Manga.title) \
                .all()
        else:
            directory = qry.filter(and_(Manga.title.ilike(u'{q}%'.format(q=alphabet[q])), Manga.chapter_count > 0)) \
                .order_by(Manga.title) \
                .all()

        LOG.debug(alphabet[q])

        return MangaApi._card_fill(_, directory)

    @view_config(route_name="series_manga", renderer='json', request_method='POST')
    def series_page(self):
        _ = self.R
        slug = _.matchdict.get('series_slug', "No Title")
        present = arrow.utcnow()
        qry = Manga.query
        manga = qry.filter(Manga.slug == slug.strip()).first()
        if manga is not None:
            filename = '/'.join([manga.id, manga.thumb])
            thumb = _.storage.url(filename)
            aka = manga.aka
            artists = manga.get_artist()
            authors = manga.get_authors()
            description = manga.description
            name = manga.title
            status = manga.status
            stags = manga.get_genre_tostr()
            tags = [dict(label=tag, value=slugist(tag)) for tag in stags.split(',')]
            time = arrow.get(manga.chapter_updated.replace(tzinfo=tz.tzlocal())).humanize(present)
            origin = manga.origin
            last = Manga.last_chapter(manga.id)

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
                        url='/'.join([manga.slug, chapter.slug]),
                        time=arrow.get(chapter.updated.replace(tzinfo=tz.tzlocal())).humanize(present)
                    ))

            return dict(
                origin=origin,
                aka=aka,
                url='/manga/{slug}'.format(slug=slug),
                thumb_url='/{thumb}'.format(thumb=thumb),
                artists=artists,
                authors=authors,
                description=description,
                name=name,
                tags=tags,
                status=status,
                time=time,
                last_chapter=last_chapter,
                last_url=last_url,
                chapters=results
            )
        return None

    @view_config(route_name='chapter_manga', renderer='json', request_method='POST')
    def chapter_view(self):
        """
            pages: [],
                name: '',
                series_name: '',
                next_chapter_url: null,
                prev_chapter_url: null
        :return:
        """
        _ = self.R
        slug = _.matchdict.get('series_slug', "No Title")
        chap_slug = _.matchdict.get('chapter_slug', "No Title")

        # cari manga by slug
        manga = Manga.query.filter(Manga.slug == slug).first()
        manga.updated_viewed()
        # LOG.debug(manga.slug)
        # cari chapter manga
        chapter = manga.get_chapter(manga, chap_slug)

        # find prev and next chapter from sortorder chapter
        prev_ch = manga.get_prev(manga, chapter)
        if prev_ch is not None:
            LOG.debug(prev_ch.slug)
            prev_ch = '/chapter/{slug}/{chap}'.format(slug=slug, chap=prev_ch.slug)

        next_ch = manga.get_next(manga, chapter)
        if next_ch is not None:
            LOG.debug(next_ch.slug)
            next_ch = '/chapter/{slug}/{chap}'.format(slug=slug, chap=next_ch.slug)

        # LOG.debug(''.format(msg=))
        path = _.storage.base_path

        manga_list = MangaUtil(path, manga.id, chapter.id)

        manga_list.build_image_lookup_dict()
        """
            /store/{manga_id}/{chapter_id/filenames
            untuk folder manga storage digunakan gendID manga e.g /store/2589637412/897589647/filenames
        """

        page_img = []
        for item in manga_list.items:
            # LOG.debug(manga_list.get_item_by_key(item)[1])
            filename = '/'.join([manga.id, chapter.id, manga_list.get_item_by_key(item)[1]])
            urlmanga = '/{thumb}'.format(thumb=_.storage.url(filename))
            # urlmanga = _.static_url('niimanga:rak/manga/{manga_id}/{chapter_id}/{file}'
            #                         .format(manga_id=manga.id,
            #                                 chapter_id=chapter.id,
            #                                 file=manga_list.get_item_by_key(item)[1]))
            page_img.append(urlmanga)
            ch = chapter.title if chapter.title == str(chapter.chapter)\
                .replace('.0', '') else '{ch} {chapter}'\
                .format(ch=str(chapter.chapter).replace('.0', ''), chapter=chapter.title)
        return dict(
            url='/chapter/{slug}/{chap}'.format(slug=slug, chap=chap_slug),
            pages=page_img,
            name='{title} {ch} - niimanga.net'.format(
                ch=ch,
                title=manga.title
            ),
            description='Read newest {title} {ch} {chapter} online'.format(
                ch=str(chapter.chapter).replace('.0', ''),
                chapter=chapter.title,
                title=manga.title
            ),
            series_url=manga.slug,
            next_chapter_url=next_ch,
            prev_chapter_url=prev_ch
        )

    @view_config(route_name='search_series', renderer='json')
    def search_series(self):
        _ = self.R
        q = _.params.get('q', ' ')
        qry = Manga.query
        results = qry.filter(and_(Manga.title.ilike(u'%{q}%'.format(q=q)), Manga.chapter_count > 0)) \
            .order_by(desc(Manga.chapter_updated)) \
            .all()
        if results:
            return MangaApi._card_fill(_, results)
        return dict(error='there is error from Manga Record Collections')

    @view_config(route_name='upload_chapter',
                 request_method='POST', renderer='json')
    def upload_chapter(self):
        _ = self.R
        # simpan di temps/uuid/
        post = _.POST
        uuid, f = post['uuid'], post['DROPZONE']
        fupload = '/'.join(['temps', uuid])

        if not _.storage.exists(fupload):
            _.storage.save(f, folder=fupload)
            # filezip = _.storage.path('/'.join([fupload, f.filename]))
            # extract_zip(filezip,  _.storage.path(fupload))
            LOG.debug('okey')
        LOG.debug(_.storage.url(fupload))
        # return HTTPSeeOther(request.route_url('home'))
        return dict(status=200)

    @view_config(route_name='list_genres', renderer='json')
    def list_genre(self):
        _ = self.R
        rows = []
        with ResponseHTTP(_.response) as resp:
            _in = u'Failed'
            code, status = ResponseHTTP.BAD_REQUEST
            q = _.params.get('q', None)
            if q is not None:
                genres = Genre.query.filter(Genre.name.ilike(u'%{q}%'.format(q=q))).all()
                for gen in genres:
                    rows.append(dict(
                        label=str(gen.name).capitalize(),
                        value=gen.slug
                    ))
                _in = u'Success'
                code, status = ResponseHTTP.OK
        return resp.to_json(_in,
                            code=code,
                            status=status, rows=rows)

    @view_config(route_name='search_genre', renderer='json')
    def search_genre(self):
        _ = self.R
        q = _.params.get('q', '')
        qry = Manga.query
        results = qry.filter(Manga.chapter_count > 0) \
            .join(Manga.genres).filter(Genre.slug == q) \
            .all()

        return MangaApi._card_fill(_, results)

    @view_config(route_name='chapter_manga_one', renderer='json', request_method='POST')
    def chapter_one_view(self):
        """
            pages: [],
                name: '',
                series_name: '',
                next_chapter_url: null,
                prev_chapter_url: null
        :return:
        """
        _ = self.R
        slug = _.matchdict.get('series_slug', "No Title")
        chap_slug = _.matchdict.get('chapter_slug', "No Title")
        page = _.matchdict.get('page', 0)

        # cari manga by slug
        manga = Manga.query.filter(Manga.slug == slug).first()
        manga.updated_viewed()

        # LOG.debug(manga.slug)
        # cari chapter manga
        chapter = manga.get_chapter(manga, chap_slug)

        results_ch = []
        # combo box all chapters
        chapters = Chapter.query.filter_by(tb_manga_id=manga.id).order_by(desc(Chapter.sortorder)).all()
        for chp in chapters:
            ch = chp.title if chp.title == str(chp.chapter) \
                .replace('.0', '') else '{ch} {chapter}' \
                .format(ch=str(chp.chapter).replace('.0', ''), chapter=chp.title)
            results_ch.append(dict(
                name=' '.join(['Ch.', ch]),
                url='/'.join([manga.slug, chp.slug, '0']),
                current=True if chp.slug == chapter.slug else False
            ))

        # LOG.debug(''.format(msg=))
        path = _.storage.base_path

        manga_list = MangaUtil(path, manga.id, chapter.id)

        manga_list.build_image_lookup_dict()        

        # find prev and next chapter from sortorder chapter
        prev_ch = manga.get_prev(manga, chapter)
        prev_ch_url = None
        # prev page
        prev_page = None
        prev_page = '/chapter/{slug}/{chap}/{page}'.format(slug=slug, chap=chap_slug, page=str(int(page)-1))
                    
        if prev_ch is not None:
            LOG.debug(prev_ch.slug)
            prev_ch_url = '/chapter/{slug}/{chap}/{page}'.format(slug=slug, chap=prev_ch.slug, page='0')
            if int(page) == 0:    
                manga_list_prev = MangaUtil(path, manga.id, prev_ch.id)
                manga_list_prev.build_image_lookup_dict()
                LOG.debug(len(manga_list_prev.get_keys()))
                prev_page = '/chapter/{slug}/{chap}/{page}'.format(slug=slug, chap=prev_ch.slug, page=str(len(manga_list_prev.get_keys())-1))   
        elif int(page) == 0:
            prev_page = None

        next_ch = manga.get_next(manga, chapter)
        next_ch_url = None
        # next page
        next_page = None
        next_page = '/chapter/{slug}/{chap}/{page}'.format(slug=slug, chap=chap_slug, page=str(int(page)+1))            
        if next_ch is not None:
            LOG.debug(next_ch.slug)
            next_ch_url = '/chapter/{slug}/{chap}/{page}'.format(slug=slug, chap=next_ch.slug, page='0')
            if int(page)+1 == len(manga_list.get_keys()):            
                next_page = next_ch_url
        elif int(page)+1 == len(manga_list.get_keys()):
            next_page = None

        page_img = []
        filename = '/'
        urlmanga = '/{thumb}'.format(thumb=_.storage.url(filename))

        if int(page) < len(manga_list.get_keys()):
            item = manga_list.get_keys()[int(page)]
            # LOG.debug(len(manga_list.get_keys()))
            filename = '/'.join([manga.id, chapter.id, manga_list.get_item_by_key(item)[1]])
            # urlmanga = '/{thumb}'.format(thumb=_.storage.url(filename))
            # LOG.debug(filename)
            # LOG.debug(_.route_url('thumbs', size='mobile', path=filename))
            size = 'web'
            mobiles = ('Android', 'webOS', 'iPhone', 'iPad', 'iPod', 'BlackBerry', 'IEMobile', 'Opera Mini')
            for mobile in mobiles:
                if mobile in _.headers['User-Agent']:
                    size = 'mobile'
            urlmanga = _.route_url('thumbs', size=size, path=filename)
            # google_search = GoogleSearch('{title} {ch} translation'
            #                              .format(ch=str(chapter.chapter).replace('.0', ''), title=manga.title))
            # google_search.start_search(max_page=3)
            # urls = google_search.search_result
            transhit = ''
            # for url in urls:
            #     try:
            #         headers = {
            #             'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/24.0'
            #         }
            #         transhit = clean_html(requests.get(url, headers=headers).text)
            #         break
            #     except requests.ConnectionError:
            #         LOG.debug("Connection to %s failed" % (str(url)))
        # LOG.debug(transhit)
        page_img.append(urlmanga)
        ch = chapter.title if chapter.title == str(chapter.chapter) \
            .replace('.0', '') else '{ch} {chapter}' \
            .format(ch=str(chapter.chapter).replace('.0', ''), chapter=chapter.title)
        return dict(
            url='/chapter/{slug}/{chap}/{page}'.format(slug=slug, chap=chap_slug, page='0'),
            pages=page_img,
            name='{title} {ch}'.format(
                ch=ch,
                title=manga.title
            ),
            description='Newest {title} {ch} online'.format(
                ch=ch,
                title=manga.title
            ),
            genres=manga.get_genre_tostr(),
            series_url=manga.slug,
            next_chapter_url=next_ch_url,
            prev_chapter_url=prev_ch_url,
            next_page_url=next_page,
            prev_page_url=prev_page,
            chapter_list=results_ch,
            page_count=dict(page=int(page), count=len(manga_list.get_keys())),
            translation=transhit
        )

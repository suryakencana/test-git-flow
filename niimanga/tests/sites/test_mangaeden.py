"""
 # Copyright (c) 06 2015 | surya
 # 18/06/15 nanang.ask@kubuskotak.com
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
 #  test_mangaeden.py
"""
import json
from unittest import TestCase, main

from niimanga.sites.mangaedenapi import MangaEdenApi

site = MangaEdenApi()


class SeriesInfo(TestCase):
    def test_normal(self):
        # url = 'http://www.mangaeden.com/en-manga/nisekoi/'
        url = 'http://localhost:8234/Nisekoi%20-%20Manga%20Eden%20-%20Read%20Manga%20Online%20Free.html'
        info = site.series_info(site.fetch_manga_seed_page(url))
        print(json.dumps(info, sort_keys=True, indent=4, separators=(',', ': ')))
        self.assertIsInstance(info, dict)

        # Attributes that can be asserted by exact value:
        expected = {
            'name': 'Nisekoi Manga',
            'site': 'mangaeden',
            'thumb_url': '//cdn.mangaeden.com/mangasimg/200x/6d/6d68be59ca2bf5e26574c07c004e8e235c8427714372440d6f130fff.jpg',
            'tags': ['shounen', 'comedy', 'romance', 'school life', 'drama', 'ecchi', 'harem'],
            'authors': ['komi naoshi'],
            'status': 'ongoing',
        }
        for key, val in expected.iteritems():
            print '>>> Asserting', key
            print '>>>>>>', info[key]
            print '======================='
            self.assertEqual(info[key], val)

        # The rest:

        self.assertIsInstance(info['description'], unicode)
        # for d in info['description']:
        #     self.assertIsInstance(d, unicode)

        self.assertIsInstance(info['status'], unicode)

        chapters = info['chapters']
        print(len(chapters))
        self.assertIsInstance(chapters, list)
        self.assertTrue(len(chapters) == 187)
        for chap in chapters:
            self.assertIsInstance(chap, dict)
            self.assertIn('url', chap)
            self.assertIn('name', chap)


class SearchByAuthor(TestCase):
    def test_normal(self):
        series_list = site.search_by_author('Fujiko F. Fujio')
        print '>>> Got list:'
        for s in series_list:
            print s
        self.assertEquals(series_list, [
            {
                'url': u'/en-manga/daichohen-doraemon/',
                'name': u'Daichohen Doraemon',
                'site': 'mangaeden'
            },
            {
                'url': u'/en-manga/doraemon-plus/',
                'name': u'Doraemon Plus',
                'site': 'mangaeden'
            },
            {
                'url': u'/en-manga/doraemon/',
                'name': u'Doraemon',
                'site': 'mangaeden'
            },
            {
                'url': u'/en-manga/dorabase-doraemon-chouyakyuu-gaiden/',
                'name': u'Dorabase: Doraemon Chouyakyuu Gaiden',
                'site': 'mangaeden'
            },
            {
                'url': u'/en-manga/daichouhen-doraemon/',
                'name': u'Daichouhen Doraemon',
                'site': 'mangaeden'
            },
            {
                'url': u'/en-manga/chinpui/',
                'name': u'Chinpui',
                'site': 'mangaeden'
            },
            {
                'url': u'/en-manga/the-doraemons/',
                'name': u'The Doraemons',
                'site': 'mangaeden'
            },
            {
                'url': u'/en-manga/the-doraemons---doraemon-game-comic/',
                'name': u'The Doraemons - Doraemon Game Comic',
                'site': 'mangaeden'
            }
        ])


class SearchLatest(TestCase):
    def test_normal(self):
        print(json.dumps(site.search_latest(), sort_keys=True, indent=4, separators=(',', ': ')))


class ChapterPages(TestCase):
    def test_normal(self):
        html = site.fetch_chapter_seed_page('http://www.mangaeden.com/en-manga/nisekoi/175/1/')
        # html = site.fetch_chapter_seed_page('http://localhost:8234/Nisekoi%20175%20%20Nisekoi%20175%20%20-%20Manga%20Eden%20-%20Read%20Manga%20Online%20Free.html')
        print(json.dumps(site.chapter_info(html), sort_keys=True, indent=4, separators=(',', ': ')))


class LatestToDB(TestCase):
    def test_normal(self):
        sites = site.search_latest()
        for source in sites[:2]:
            resp_content = site.get_html(source["last_url"])

            series = site.series_info(resp_content)
            for chapter in series["chapters"][:2]:
                chapter_url = site.get_html(chapter["url"])
                chapters = site.chapter_info(chapter_url)
                print(chapters)


if __name__ == '__main__':
    main()

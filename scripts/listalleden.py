"""
 # Copyright (c) 09 2015 | surya
 # 17/09/15 nanang.ask@kubuskotak.com
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
 #  listalleden.py
"""
import logging

from niimanga.sites import MangaEdenApi
from pymongo import MongoClient
import pymongo

LOG = logging.getLogger(__name__)
site = MangaEdenApi()


"""
python scripts/mangascrapper.py -s https://www.mangaeden.com/api/manga/4e70ea1dc092255ef7004d5c/ -o http://www.mangaeden.com/en/en-manga/fairy-tail/ -t "Aug 31, 2015"
:return:
"""
try:
    conn = MongoClient('localhost', 27017)
    db = conn["niimanga"]
    leden = db.listeden

    series_api_url = "https://www.mangaeden.com/api/manga/"
    series_url = "http://www.mangaeden.com/en/en-manga/"

    for seri in leden.find().sort('h', pymongo.DESCENDING).limit(1000)[600:]:
        url = "{url}{slug}".format(url=series_url, slug=seri.get("a"))
        api_url = "{url}{slug}".format(url=series_api_url, slug=seri.get("i"))
        print(url)
        site.script_to_sys(api_url, url, seri.get("ld"))
    print("---it's done---")

except Exception as e:
    print(e.message)
    LOG.debug(e.message)

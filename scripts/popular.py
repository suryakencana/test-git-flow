"""
 # Copyright (c) 08 2015 | surya
 # 05/08/15 nanang.ask@kubuskotak.com
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
 #  popular.py
"""
from niimanga.ctasks.batoto import build_to_sys
from niimanga.sites.batoto import Batoto


site = Batoto()

try:
    for i, source in enumerate(site.search_popular()):
        # LOG.info(source)
        print(source)
        build_to_sys(site, source)
except Exception as e:
    print(e.message)
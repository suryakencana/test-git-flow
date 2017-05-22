"""
 # Copyright (c) 03 2016 | suryakencana
 # 3/23/16 nanang.ask@kubuskotak.com
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
 #  goog.py
"""

from bs4 import BeautifulSoup
import requests
import re


class GoogleSearch(object):
    """Class to initiate a query to google.com.

    Require only keyword.
    Initiation of this class is not yet queried to google.com.

    """

    def __init__(self, keyword):
        """The required initial is only keyword."""
        kwd = keyword.strip()
        self.query = "q=%s" % (kwd.replace(" ", "+"))
        self.is_final_page = False
        self.request_page = None
        self.current_page = 1
        self.current_html_page = ''
        self.search_result = []
        self.google = "http://www.google.com/search?"

    def start_search(self, max_page=1):
        """method to start send query to google. Search start from page 1.

        max_page determine how many result expected
        hint: 10 result per page for google
        """
        for page in range(1, (max_page + 1)):
            start = "start=%s" % str((page - 1) * 10)
            url = "%s%s&%s" % (self.google, self.query, start)
            self._execute_search_request(url)
            self.current_page += 1

    def more_search(self, more_page):
        """Method to add more result to an already exist result.

        more_page determine how many result page should be added
        to the current result.
        """
        next_page = self.current_page + 1
        top_page = more_page + self.current_page
        for page in range(next_page, (top_page + 1)):
            start = "start=%s" % str((page - 1) * 10)
            url = "%s%s&%s" % (self.google, self.query, start)
            self._execute_search_request(url)
            self.current_page += 1

    def _execute_search_request(self, url):
        """method to execute the query to google.

        The specified page and keyword
        must already included in the url.
        """
        try:
            self.request_page = requests.get(url)
        except requests.ConnectionError:
            print("Connection to %s failed" % (str(url)))
        self.current_html_page = self.request_page.text
        soup = BeautifulSoup(self.current_html_page, "html5lib")
        results = soup.find_all('a', class_=False)
        links = []  # store the final url of search result, 10 links
        # this loop filter the search result links inside the search page
        for target in results:
            # filter only link from search result should be appended
            if target.get('href').find("/url?q") == 0 \
                    and not \
                    target.get('href').find(
                            "/url?q=http://webcache.googleusercontent.com"
                    ) == 0 \
                    and not \
                    target.get('href').find("/url?q=/settings/") == 0:
                start_index = target.get('href').find('http')
                end_index = target.get('href').find('&sa')
                # slice the desired url into ideal link, and append
                # it to reserved list variable
                links.append(target.get('href')[start_index:end_index])
        # this loop inspect if the current page is the final page
        for href in results:
            fnl = 'repeat the search with the omitted results included'
            if href.get_text() == fnl:
                self.is_final_page = True
            else:
                pass
        # send the final url link to class reserved variable
        for link in links:
            self.search_result.append(link)


def clean_html(html):
    """
    Remove HTML markup from the given string. Borrowed from nltk.
    """
    # First we remove inline JavaScript/CSS:
    cleaned = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", "", html.strip())
    # Then we remove html comments. This has to be done before removing regular
    # tags since comments can contain '>' characters.
    cleaned = re.sub(r"(?s)<!--(.*?)-->[\n]?", "", cleaned)
    # Next we can remove the remaining tags:
    cleaned = re.sub(r"(?s)<.*?>", " ", cleaned)
    # Finally, we deal with whitespace
    cleaned = re.sub(r"&nbsp;", " ", cleaned)
    cleaned = re.sub(r"  ", " ", cleaned)
    cleaned = re.sub(r"  ", " ", cleaned)
    cleaned = cleaned.strip('\n')
    cleaned = cleaned.strip('\t')
    cleaned = ' '.join(cleaned.split())
    return cleaned.strip()

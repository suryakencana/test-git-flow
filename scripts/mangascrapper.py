"""
 # Copyright (c) 09 2015 | surya
 # 03/09/15 nanang.ask@kubuskotak.com
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
 #  mangascrapperr.py
"""
import sys
import argparse

from niimanga.sites import MangaEdenApi, Batoto


def check_negative(value):
    """
    Checks for Negative values in arguments.

    :param value: Value whose positive nature is checked.
    :return: Returns value if not negative.
    :rtype: int
    :raise argparse.ArgumentTypeError:
    """
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return ivalue


def main():
    """
    Main Method and UI/CLI for the MangaScrapper.

    :raise OSError: Error in case the storage location is invalid, or some other
    errors has occurred.
    """
    desc = "MangaScrapper is simple, easy, and fast CLI tool to download manga's " \
           "and also create an ebook in pdf format."

    parser = argparse.ArgumentParser(description=desc, prog="mangascrapper.py")
    parser.add_argument('-w', '--site', type=str, help="The website where manga has to be downloaded. ")
    parser.add_argument('-s', '--source', type=str, help="The source where manga has to be downloaded. ")
    parser.add_argument('-o', '--origin', type=str, help="The link where manga has to be downloaded. ")
    parser.add_argument('-t', '--time', type=str, help="The time where latest chapter manga has to be downloaded. ")
    parser.add_argument('-d', '--timestamp', type=float,
                        help="The time where latest chapter manga has to be downloaded. ")
    #
    # parser.add_argument('manga_name', type=str, help="Enter the name of the manga.")
    # parser.add_argument('-b', '--begin', type=check_negative,
    #                     help="Enter the starting chapter. By default its first chapter")
    # parser.add_argument('-e', '--end', type=check_negative,
    #                     help="Enter the ending chapter. Defaults to the last chapter "
    #                          "possible.")
    # parser.add_argument('-c', '--chapter', type=check_negative,
    #                     help="Give the chapter number if you want to download only "
    #                          "one chapter.")
    # parser.add_argument('-l', '--location', type=str, help="The location where manga has to be downloaded. "
    #                                                        "By default stored in the current directory.",
    #                     default=os.getcwd())
    # parser.add_argument('-lc', '--latest', action='store_true', help="Download the latest Manga chapter")
    # parser.add_argument('-out', '--outformat', type=str, help="Generated Manga/Comic book output formats. Available "
    #                                                           "formats are cbr, cbz, cbt, & pdf; default is cbz.",
    #                     default="cbz")

    args = parser.parse_args()

    # if args.chapter and (args.begin or args.end):
    #     print("--chapter argument cannot be used along with --begin/--end. \n")
    #     parser.parse_args(["--help"])
    # elif args.chapter and args.latest:
    #     print("--chapter argument cannot be used along with --latest \n")
    #     parser.parse_args(["--help"])
    # elif args.latest and (args.begin or args.end):
    #     print("--latest argument cannot be used along with --begin/--end. \n")
    #     parser.parse_args(["--help"])
    # else:
    #     if args.location and not os.path.isdir(args.location):
    #         raise OSError("The given save location is not valid. It must be a directory.")
    #     elif not os.access(args.location, os.W_OK):
    #         raise OSError("You do not have permission to write in the given path. Run as root.")

    # if args.outformat.strip().lower() == "cbr":
    #     args.outformat = OutFormats.CBR
    # elif args.outformat.strip().lower() == "cbz":
    #     args.outformat = OutFormats.CBZ
    # elif args.outformat.strip().lower() == "cbt":
    #     args.outformat = OutFormats.CBT
    # elif args.outformat.strip().lower() == "pdf":
    #     args.outformat = OutFormats.PDF
    time_local = None
    if args.timestamp:
        time_local = args.timestamp
    if args.time:
        time_local = args.time
    print(args.site)
    if args.origin:
        if "mangaeden" in args.site:
            site = MangaEdenApi()
            if args.source:
                # source digunakan untuk mangaeden source link API
                site.script_to_sys(args.source, args.origin, time_local)
        if "batoto" in args.site:
            site = Batoto()
            site.script_to_sys(args.origin, time_local)

    # if args.latest:
    # elif args.chapter:
    #     scrape = MangaScrapper(args.manga_name, args.chapter, args.chapter, args.location, args.outformat)
    # elif args.begin and args.end:
    #     if int(args.begin) < int(args.end):
    #         scrape = MangaScrapper(args.manga_name, args.begin, args.end, args.location, args.outformat)
    #     else:
    #         raise AttributeError("begin must be smaller than end chapter")
    # elif args.begin:
    #     scrape = MangaScrapper(args.manga_name, args.begin, None, args.location, args.outformat)
    # elif args.end:
    #     scrape = MangaScrapper(args.manga_name, None, args.end, args.location, args.outformat)
    # else:
    #     raise Exception("Unknown Error")
    #     # scrape.start_scrapping()


if __name__ == "__main__":
    sys.exit(main())

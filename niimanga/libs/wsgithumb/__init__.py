# -*- coding: utf-8 -*-
import logging
import os
from hashlib import md5
import stat
from .utils import get_file_response, compress_pil
from .utils import HTTPNotFound
from .utils import resize

LOG = logging.getLogger(__name__)

try:
    unicode
    PY3 = False
except NameError:
    unicode = str
    PY3 = True


DEFAULT_SIZES = {
    'icon': (16, 16),
    'small': (50, 50),
    'thumb': (100, 100),
    'medium': (300, 300),
    'large': (500, 500),
    'xlarge': (800, 800),
    'original': None,
    }


def get_image_response(document_root=None, cache_directory=None,
                       size=(500, 500), factor=100,
                       path=None, accel_header=None):
    """helper the get an image response"""
    # FIXME cache_directory can't be None

    dummy, ext = os.path.splitext(path)

    # make sure we got an image
    if ext.lower() not in ('.png', '.jpg', '.jpeg', '.gif'):
        return HTTPNotFound()

    if PY3:
        filename = os.path.join(document_root, path)
    else:
        filename = os.path.join(document_root, path.encode('utf-8'))
    if not os.path.isfile(filename):
        return HTTPNotFound()

    if size is None:
        # get original
        return get_file_response(filename,
                                 accel_header=accel_header,
                                 document_root=document_root)

    factor = int(factor)

    # generate cached direname
    h = u'%s-%s-%s' % (path, size, factor)
    if PY3 or isinstance(h, unicode):
        h = h.encode('utf8')
    h = md5(h).hexdigest()
    d1, d2, d3 = h[0:3], h[3:6], h[6:9]

    cached = os.path.join(cache_directory, d1, d2, d3)
    if not os.path.isdir(cached):
        try:
            os.makedirs(cached)
        except OSError:
            # dir exist...?!
            pass

    cached = os.path.join(cached, os.path.basename(filename))

    if os.path.isfile(cached):
        last_modified = os.stat(filename)[stat.ST_MTIME]
        last_cached = os.stat(cached)[stat.ST_MTIME]
        if last_modified > last_cached:
            os.remove(cached)
    LOG.debug(filename)
    LOG.debug(cached)

    # generate cached thumb if not yet done
    if not os.path.isfile(cached):
        LOG.debug(size)
        if isinstance(size, tuple):
            print('---tuple---')
            resize(filename, cached, size, factor=factor)
        else:
            compress_pil(filename, cached, size)

    return get_file_response(cached,
                             document_root=cache_directory,
                             accel_header=accel_header)


def add_file_view(config, route_name, sizes=DEFAULT_SIZES,
                  document_root=None, cache_directory=None, **view_args):
    """add a view to serve files in pyramid"""
    settings = config.registry.settings

    if not document_root:
        document_root = settings['files.document_root']
    document_root = os.path.abspath(document_root)

    accel_header = settings.get('files.accel_header', None)

    def view(request):
        path = request.matchdict['path']
        path = '/'.join(path)
        filename = os.path.join(document_root, path)
        return get_file_response(
            filename,
            document_root=document_root,
            accel_header=accel_header
        )

    config.add_route(route_name, '/%s/*path' % route_name)
    config.add_view(view, route_name=route_name, **view_args)


def add_thumb_view(config, route_name, sizes=DEFAULT_SIZES, factors=(),
                   document_root=None, cache_directory=None, **view_args):
    """add a view to serve thumbnails in pyramid"""
    settings = config.registry.settings

    if not document_root:
        document_root = settings['thumbs.document_root']
    document_root = os.path.abspath(document_root)

    if not cache_directory:
        cache_directory = settings['thumbs.cache_directory']
    cache_directory = os.path.abspath(cache_directory)

    if not os.path.isdir(cache_directory):
        os.makedirs(cache_directory)

    accel_header = settings.get('thumbs.accel_header', None)

    def view(request):
        size = sizes[request.matchdict['size']]
        factor = int(request.matchdict.get('factor', 100))
        if factors and factor not in factors:
            return HTTPNotFound()
        path = request.matchdict['path']
        path = '/'.join(path)
        return get_image_response(
            document_root=document_root,
            cache_directory=cache_directory,
            size=size, factor=factor, path=path, accel_header=accel_header
        )

    if factors:
        config.add_route(route_name, '/%s/{size}/{factor}/*path' % route_name)
    else:
        config.add_route(route_name, '/%s/{size}/*path' % route_name)
    config.add_view(view, route_name=route_name, **view_args)


def includeme(config):
    """pyramid include. declare the add_thumb_view"""
    config.add_directive('add_thumb_view', add_thumb_view)
    config.add_directive('add_file_view', add_file_view)


def make_thumb_app(global_conf, document_root=None,
                   cache_directory=None,
                   accel_header=None,
                   sizes=DEFAULT_SIZES,
                   factors=(),
                   **settings):
    """thumb application factory"""
    document_root = os.path.abspath(document_root)

    cache_directory = os.path.abspath(cache_directory)

    if not os.path.isdir(cache_directory):
        os.makedirs(cache_directory)

    def application(environ, start_response):
        path_info = environ['PATH_INFO'].strip('/')
        try:
            size, path = path_info.split('/', 1)
        except ValueError:
            return HTTPNotFound()(environ, start_response)
        if size not in DEFAULT_SIZES:
            return HTTPNotFound()(environ, start_response)
        size = sizes[size]
        return get_image_response(
            document_root=document_root,
            cache_directory=cache_directory,
            size=size, path=path, accel_header=accel_header
        )(environ, start_response)

    return application


def make_file_app(global_conf, document_root=None,
                  accel_header=None,
                  **settings):
    """file application factory"""
    document_root = os.path.abspath(document_root)

    def application(environ, start_response):
        path_info = environ['PATH_INFO'].strip('/')
        filename = os.path.join(document_root, path_info)
        return get_file_response(
            filename=filename,
            document_root=document_root,
            accel_header=accel_header
        )(environ, start_response)

    return application

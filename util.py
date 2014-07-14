# -*- coding:utf-8 -*-
import os
import logging
import mimetypes
import web

def serve_file(file_path, content_type=None):
    logging.debug("Static file: '%s'" % file_path)

    filename = os.path.basename(file_path)
    logging.debug("Filename: '%s'" % filename)

    try:
        fil = open(file_path, "r")
    except IOError:
        logging.error("File not found")
        raise web.notfound()

    if content_type is None:
        ftype = mimetypes.guess_type(filename)[0]
    else:
        ftype = content_type

    if ftype:
        logging.debug("File type: %s" % ftype)
        web.header("Content-Type", ftype)
    else:
        logging.error("Could not guess file type")

    return fil.read()

class StaticDirHandler:
    path = None
    def GET(self, filename=None):
        assert filename is not None
        assert self.path is not None

        full_filename = os.path.join(self.path, filename)
        return serve_file(full_filename)

class StaticFileHandler:
    file_path = None
    content_type = None

    def GET(self):
        assert self.file_path is not None
        return serve_file(self.file_path, self.content_type)

class StrictHandler:
    def GET(self):
        raise web.notfound()

    def POST(self):
        raise web.notfound()


class render_mako:
    """Rendering interface to Mako Templates, with cache.

    Example:

        render = render_mako(directories=['templates'])
        render.hello(name="mako")
    """
    def __init__(self, *a, **kwargs):
        from mako.lookup import TemplateLookup
        self._lookup = TemplateLookup(*a, **kwargs)

    def __getattr__(self, name):
        # Assuming all templates are html
        path = name + ".html"
        t = self._lookup.get_template(path)
        return t.render

    def __getitem__(self, key):
        #可以使用直接访问到模板对象
        path = key + ".html"
        t = self._lookup.get_template(path)
        return t

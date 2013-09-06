#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import os
import StringIO

import jinja2
import webapp2
from PIL import Image

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import ndb

import meme


TODO = None

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'])

MEME_TEMPLATES = collections.OrderedDict([
    ('happyboy', 'happyboy.jpeg'),
    ('rapperboy', 'rapperboy.jpeg'),
    ('realappengine', 'realappengine.jpeg'),
    ('shrugging', 'shrugging.jpeg'),
    ('bathing', 'bathing.jpeg'),
])

DEFAULT_TEMPLATE = 'happyboy.jpeg'

IMAGE_DIR = 'images'

MEME_FONTS = collections.OrderedDict([
    ('mikachan', 'mikachan.ttf'),
    ('FreeSerif', 'FreeSerif.ttf'),
])

DEFAULT_FONT = 'FreeSerif.ttf'

FONT_DIR = 'fonts'

THUMBNAIL_SIZE = (400, 400)

PAGE_SIZE = 40

MEMCACHE_RECENT_KEY = 'recent'


def get_login_logout_context(target_url):
    """Returns nickname, link url and link text for the common_header.html."""
    user = users.get_current_user()
    if user:
        nickname = user.nickname()
        link_text = 'Logout'
        link_url = users.create_logout_url(target_url)
    else:
        nickname = 'Anonymous user'
        link_text = 'Login'
        link_url = users.create_login_url(target_url)
    return nickname, link_url, link_text


class MainHandler(webapp2.RequestHandler):
    """A handler for showing an HTML form."""

    def get(self):
        """Render an HTML form for creating Memes."""
        template = JINJA_ENV.get_template('index.html')
        nickname, link_url, link_text = get_login_logout_context(
            self.request.uri)
        context = {
            'templates': MEME_TEMPLATES,
            'fonts': MEME_FONTS,
            'nickname': nickname,
            'link_text': link_text,
            'link_url': link_url
        }
        self.response.out.write(template.render(context))


class ImageHandler(webapp2.RequestHandler):
    """A handler for rendering and saving Memes."""

    def render_meme(self):
        """Renders an image with given HTTP parameters.

        Returns:
            A rendered Image object.
        """
        meme_template = self.request.get('meme_template')
        image = Image.open(os.path.join(IMAGE_DIR,
            MEME_TEMPLATES.get(meme_template, DEFAULT_TEMPLATE)))
        meme_font = self.request.get('meme_font')
        font_file = os.path.join(FONT_DIR,
                                 MEME_FONTS.get(meme_font, DEFAULT_FONT))
        upper_text = self.request.get('upper_text')
        upper_text_align = self.request.get('upper_text_align', meme.MIDDLE)
        middle_text = self.request.get('middle_text')
        middle_text_align = self.request.get('middle_text_align', meme.MIDDLE)
        lower_text = self.request.get('lower_text')
        lower_text_align = self.request.get('lower_text_align', meme.MIDDLE)
        if upper_text:
            meme.draw_text(image, meme.TOP, upper_text_align, upper_text,
                           font_file=font_file)
        if middle_text:
            meme.draw_text(image, meme.MIDDLE, middle_text_align, middle_text,
                           font_file=font_file)
        if lower_text:
            meme.draw_text(image, meme.BOTTOM, lower_text_align, lower_text,
                           font_file=font_file)
        return image

    def get(self):
        """A handler for rendering a preview image."""
        image = self.render_meme()
        self.response.headers['Content-Type'] = 'image/jpg'
        image.save(self.response.out, 'JPEG')

    def post(self):
        """A handler for save the meme."""
        image = self.render_meme()
        new_meme = meme.Meme()
        user = users.get_current_user()
        if user:
            new_meme.owner = user
        output = StringIO.StringIO()
        thumbnail_output = StringIO.StringIO()
        image.save(output, "JPEG")
        image.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)
        image.save(thumbnail_output, "JPEG")
        new_meme.image = output.getvalue()
        new_meme.thumbnail = thumbnail_output.getvalue()
        output.close()
        thumbnail_output.close()
        new_meme.put()
        # step-3
        # It is important to delete the cache here for recent query.
        # Otherwise, the 'Recent' page will keep serving an old list.
        memcache.delete(MEMCACHE_RECENT_KEY)
        self.redirect("/meme/{}".format(new_meme.key.id()), abort=True)


class MemeHandler(webapp2.RequestHandler):
    """A handler for rendering an HTML page of a particular meme."""

    def get(self, meme_id):
        """Renders an HTML page of a Meme with a given id.

        Raises a 404 error when entity not found.

        Args:
            meme_id: id of Meme entity extracted from the URL path.
        """
        target = meme.Meme.get_by_id(long(meme_id))
        if target is None:
            self.abort(404)
        nickname, link_url, link_text = get_login_logout_context(
            self.request.uri)
        template = JINJA_ENV.get_template('meme.html')
        if target.owner:
            owner_nickname = target.owner.nickname()
        else:
            owner_nickname = 'Anonymous user'
        context = {
            'nickname': nickname,
            'link_url': link_url,
            'link_text': link_text,
            'meme_owner': owner_nickname,
            'meme_id': target.key.id(),
            'meme_created_date': target.created_at,
        }
        self.response.write(template.render(context))


class MemeImageHandler(webapp2.RequestHandler):
    """A handler for serving an image of a particular meme."""

    def get(self, mode, meme_id):
        """Serves an image of a particular meme.

        Raises a 404 error when entity not found.

        Args:
            mode: 'image' or 'thumbnail', extracted from the URL path.
            meme_id: id of Meme entity extracted from the URL path.
        """
        target = meme.Meme.get_by_id(long(meme_id))
        if target is None:
            self.abort(404)
        self.response.headers['Content-Type'] = 'image/jpeg'
        if mode == 'image':
            self.response.write(target.image)
        else:
            self.response.write(target.thumbnail)


class MemeListingHandler(webapp2.RequestHandler):
    """A handler for listing recent memes."""

    def get(self, mode):
        """Display a list of memes according to given conditions.

        The condition is given by the URL. Currently only 'recent' and
        'mine' are implemented.
        """
        if mode == 'recent':
            meme_keys = memcache.get(MEMCACHE_RECENT_KEY)
            if meme_keys is not None:
                memes = ndb.get_multi(meme_keys)
            else:
                # step-3
                # Complete the query object.  We want meme.Meme
                # objects ordered by the created_at in a descending
                # order.
                query = meme.Meme.query().order(-meme.Meme.created_at)
                memes = query.fetch(PAGE_SIZE)
                memcache.set(MEMCACHE_RECENT_KEY, [m.key for m in memes])
            title = 'Recent memes'
        elif mode == 'mine':
            user = users.get_current_user()
            if user is None:
                self.redirect(users.create_login_url(self.request.uri),
                              abort=True)
            query = meme.Meme.query(meme.Meme.owner==user)\
                .order(-meme.Meme.created_at)
            title = 'Your memes'
            memes = query.fetch(PAGE_SIZE)
        nickname, link_url, link_text = get_login_logout_context(
            self.request.uri)
        template = JINJA_ENV.get_template('list_meme.html')
        context = {
            'title': title,
            'nickname': nickname,
            'link_url': link_url,
            'link_text': link_text,
            'memes': memes,
        }
        self.response.write(template.render(context))


APPLICATION = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/preview', ImageHandler),
    ('/create_meme', ImageHandler),
    ('/meme/(\d+)', MemeHandler),
    ('/(image|thumbnail)/(\d+)', MemeImageHandler),
    ('/(recent|mine)', MemeListingHandler),
], debug=True)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import os

import jinja2
import webapp2
from PIL import Image

from google.appengine.api import users

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


class MainHandler(webapp2.RequestHandler):
    """A handler for showing an HTML form."""

    def get(self):
        """Render an HTML form for creating Memes."""
        template = JINJA_ENV.get_template('index.html')
        # step-1
        # Obtain information of the current signed in user.
        user = TODO
        if user:
            nickname = user.nickname()
            link_text = 'Logout'
            # step-1
            # Create a URL for loging out from the app.
            link_url = TODO
        else:
            nickname = 'Anonymous user'
            link_text = 'Login'
            link_url = users.create_login_url(self.request.uri)
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


APPLICATION = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/preview', ImageHandler),
], debug=True)

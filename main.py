#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import jinja2
import webapp2
from PIL import Image

import meme


JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

MEME_TEMPLATES = {
    'happyboy': 'happyboy.jpeg',
    'rapperboy': 'rapperboy.jpeg',
    'realappengine': 'realappengine.jpeg',
}

DEFAULT_TEMPLATE = 'happyboy.jpeg'


class MainHandler(webapp2.RequestHandler):
    """A handler for showing an HTML form."""

    def get(self):
        """Render an HTML form for creating Memes."""
        template = JINJA_ENV.get_template('index.html')
        context = {'templates': sorted(MEME_TEMPLATES.keys())}
        self.response.out.write(template.render(context))


class ImageHandler(webapp2.RequestHandler):
    """A handler for rendering and saving Memes."""

    def render_meme(self):
        """Renders an image with given HTTP parameters.

        Returns:
            A rendered Image object.
        """
        meme_template = self.request.get('meme_template')
        image = Image.open(MEME_TEMPLATES.get(meme_template, DEFAULT_TEMPLATE))
        upper_text = self.request.get('upper_text')
        upper_text_align = self.request.get('upper_text_align', meme.MIDDLE)
        middle_text = self.request.get('middle_text')
        middle_text_align = self.request.get('middle_text_align', meme.MIDDLE)
        lower_text = self.request.get('lower_text')
        lower_text_align = self.request.get('lower_text_align', meme.MIDDLE)
        if upper_text:
            meme.draw_text(image, meme.TOP, upper_text_align, upper_text)
        if middle_text:
            meme.draw_text(image, meme.MIDDLE, middle_text_align, middle_text)
        if lower_text:
            meme.draw_text(image, meme.BOTTOM, lower_text_align, lower_text)
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

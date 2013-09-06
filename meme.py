#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from google.appengine.ext import ndb


TODO = None

TOP = "top"
MIDDLE = "middle"
BOTTOM = "bottom"
LEFT = "left"
RIGHT = "right"
DEFAULT_FONT = "mikachan.ttf"
DEFAULT_FONT_SIZE = 48
DEFAULT_TEXT_COLOR = "#FFF"
DEFAULT_BORDER_COLOR = "#000"
DEFAULT_BORDER_WIDTH = 2


def get_points_for_hemming(src, border_width=1):
    """Returns a list of points described below.

    Args:
        src: (x, y) tuple indicating the source point.
        border_width: a width of the border line.

    Returns:
        List of points described as * in the following figure.

        when border=1:
        ***
        *@*
        ***

        when border=2:
        * * *

        * @ *

        * * *
    """
    x, y = src
    return [
        (x - border_width, y - border_width), (x, y - border_width),
        (x + border_width, y - border_width), (x - border_width, y),
        (x + border_width, y), (x - border_width, y + border_width),
        (x, y + border_width), (x + border_width, y + border_width),
    ]


def draw_text(target, vertical_position, horizontal_position, text,
              font_file=DEFAULT_FONT, font_size=DEFAULT_FONT_SIZE,
              color=DEFAULT_TEXT_COLOR, border_width=DEFAULT_BORDER_WIDTH,
              border_color=DEFAULT_BORDER_COLOR):
    """Draws a text at a given position in a given image.

    Args:
        target: a target image object.
        vertical_position: either of TOP|MIDDLE|BOTTOM
        horizontal_position: either of LEFT|MIDDLE|RIGHT
        text: text to draw
        font_file: font filename for drawing the text
        font_size: font size
        color: text color
        border_width: border width of the text
        border_color: border color of the text
    """
    # determine the original text size
    font = ImageFont.truetype(font_file, font_size)
    image = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(image)
    text_width, text_height = draw.textsize(text, font=font)
    del draw

    # draw text with border
    bordered_text_width = text_width + 2 * border_width
    bordered_text_height = text_height + 2 * border_width
    image = Image.new('RGBA', (bordered_text_width, bordered_text_height))
    draw = ImageDraw.Draw(image)
    for pos in get_points_for_hemming((border_width, border_width),
                                      border_width):
        draw.text(pos, text, font=font, fill=border_color)
    draw.text((border_width, border_width), text, font=font, fill=color)
    del draw

    # obtain bounding boxes for 2 images for later use
    bbox = target.getbbox()
    text_bbox = image.getbbox()

    # scale only if the text exceeds the width of the target image
    if bbox[2] < text_bbox[2]:
        scale = float(bbox[2]) / text_bbox[2]
        image = image.resize((int(text_bbox[2] * scale),
                              int(text_bbox[3] * scale)), Image.ANTIALIAS)
        text_bbox = image.getbbox()
    else:
        image = image.filter(ImageFilter.SMOOTH)

    # determine the paste position
    if vertical_position == TOP:
        pos_y = 0
    elif vertical_position == MIDDLE:
        pos_y = int(bbox[3] / 2 - text_bbox[3] / 2)
    elif vertical_position == BOTTOM:
        pos_y = bbox[3] - text_bbox[3]
    else:
        raise RuntimeError('Invalid vertical_position: {}'
                           .format(vertical_position))
    if horizontal_position == LEFT:
        pos_x = 0
    elif horizontal_position == MIDDLE:
        pos_x = int(bbox[2] / 2 - text_bbox[2] / 2)
    elif horizontal_position == RIGHT:
        pos_x = bbox[2] - text_bbox[2]
    else:
        raise RuntimeError('Invalid horizontal_position: {}'
                           .format(horizontal_position))

    target.paste(image , (pos_x, pos_y), image)


class Meme(ndb.Model):
    """A model class for storing memes."""
    # step-2
    # Fill the owner attribute, in order to save the owner info.
    # See the docs below:
    # https://developers.google.com/appengine/docs/python/ndb/properties#types
    owner = ndb.UserProperty()
    image = ndb.BlobProperty()
    thumbnail = ndb.BlobProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tweets a random Rosetta image as @RosettaBot.

Note: for setting up a bot, see
http://dghubble.com/blog/posts/twitter-app-write-access-and-bots/
"""
import random
from twython import Twython
from matplotlib.image import imsave
from matplotlib import cm

from astropy import log
from astropy.io import fits
from astropy.time import Time
from astropy.visualization import scale_image

# Our own modules
from entropy_crop import entropy_crop
from secrets import *


def select_random_image(db_fn='data/rosetta-fits-files.csv'):
    db = open(db_fn, 'r').readlines()
    idx = random.randint(0, len(db))
    return db[idx].split(',')


def generate_tweet():
    """Generate a tweet and jpg.

    Returns
    -------
    (status, jpg) : (str, str)
    """
    imageid, fitsurl = select_random_image()
    log.info('Opening {0}'.format(fitsurl))
    fts = fits.open(fitsurl)
    # Create the status message
    imgtime = fts[0].header['IMG-TIME']
    instrument = fts[0].header['INSTRUME'][8:]
    exptime = fts[0].header['EXPTIME']
    timestr = Time(imgtime).datetime.strftime('%d %b %Y, %H:%M UT').lstrip("0")
    url = 'http://imagearchives.esac.esa.int/picture.php?/{0}'.format(imageid)
    status = ('A new #Rosetta image was recently released!\n'
              '⌚ {}.\n'
              '📷 #{}.\n'
              '⌛ {:.2f}s.\n'
              '🔗 {}'.format(timestr, instrument, exptime, url))
    # Create the cropped and scaled image
    image_cropped = entropy_crop(fts[0].data, width=600, height=300)
    image_scaled = scale_image(image_cropped, scale='linear',
                               min_percent=0.05, max_percent=99.95)
    # Save the result as an image
    image_fn = '/tmp/rosettabot.png'
    log.info('Writing {0}'.format(image_fn))
    imsave(image_fn, image_scaled, cmap=cm.gray)
    return (status, image_fn)


def post_tweet(status, media_fn):
    """Post media and an associated status message to Twitter."""
    twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    upload_response = twitter.upload_media(media=open(media_fn, 'rb'))
    response = twitter.update_status(status=status,
                                     media_ids=upload_response['media_id'])
    log.info(response)
    return twitter, response


if __name__ == '__main__':
    # Failsafe: attempt multiple files until successful
    attempt_no = 0
    while attempt_no < 10:
        attempt_no += 1
        try:
            status, image_fn = generate_tweet()
            log.info(status)
            log.info('Saved {0}'.format(image_fn))
            twitter, response = post_tweet(status, image_fn)
            break
        except Exception as e:
            log.warning(e)

#!/usr/bin/env python

from os.path import join, dirname

from cloudify import ctx

ctx.download_resource(
    join('components', 'utils.py'),
    join(dirname(__file__), 'utils.py'))
import utils  # NOQA

WEBUI_SERVICE_NAME = 'webui'


ctx.logger.info('Starting WebUI Service...')
utils.start_service(WEBUI_SERVICE_NAME)

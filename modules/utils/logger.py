#!/usr/bin/env python3

import logging
import os
import sys


def setup(name="main", level=None, _format=None, debug_file=None):
    level = level if level else os.environ.get("LOGLEVEL", "INFO").upper()
    default_format = (
        "| %(levelname)s | [%(filename)s: %(lineno)d]: | %(message)s"
        if level == "DEBUG"
        else "| %(name)-6s | %(levelname)-6s | %(message)s"
    )
    # if format is truthy, use format
    # else if falsy, use default format
    _format = _format or default_format
    logging.basicConfig(level=level, stream=sys.stdout, format=_format)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if debug_file:
        formatter = logging.Formatter(_format)
        fileHandler = logging.FileHandler(debug_file)
        fileHandler.setLevel(logging.DEBUG)
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)
    return logger

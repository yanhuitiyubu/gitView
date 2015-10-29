# -*- coding: utf-8 -*-

from os.path import basename

__all__ = ('get_repo_name_from_url', 'key_generator')


def get_repo_name_from_url(repo_url):
    '''Get repository's name from its URL'''
    name = repo_url[:-2] if repo_url.endswith('/') else repo_url
    return basename(name).replace('.git', '')


def key_generator(*args, **kwargs):
    delimiter = kwargs.get('delimiter', None)
    delimiter = ',' if delimiter is None else delimiter
    return delimiter.join(args)

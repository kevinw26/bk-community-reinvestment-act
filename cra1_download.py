# -*- coding: utf-8 -*-
"""
Created on Thu Apr 25 17:35:44 2024

This does not work because of `Captcha Error` on FFIEC website, now protected by
CloudFlare. Use of CloudScraper does not resolve.

@author: Kevin.Wong
"""
import os
import itertools
import cloudscraper

from os import path
from typing import Literal
from concurrent.futures import ProcessPoolExecutor, as_completed, wait

import pandas as pd
from tqdm import tqdm

__CENSUS = 'https://www.ffiec.gov/censusapp.htm'
__ADCFFL = 'https://www.ffiec.gov/cra/craflatfiles.htm'


def download(url, to_path, overwriting=False, referrer=''):
    """
    Download some some `url` `to_path`. If `overwriting`, do so.
    """
    if path.exists(to_path) and not overwriting:
        tqdm.write(f'skipping download to {to_path}; already exists')
        return

    # see also https://stackoverflow.com/a/16696317/2741091
    s = cloudscraper.CloudScraper(delay=5, debug=True)
    with s.get(url, stream=True) as r:
        r.raise_for_status()
        with open(to_path) as f:
            for chunk in r.iter_content(chunk_size=2 ** 16):
                f.write(chunk)

        tqdm.write(f'finished download {to_path}')


def pull_file(year: int, f_type: Literal['aggr', 'trans', 'discl', 'census']):
    """
    Pull CRA file from FFIEC website by year and file type.

    Parameters
    ----------
    year : int
        to pull with the file type; must be four digits

    f_type : Literal['aggr', 'trans', 'discl', 'census']
        file type to pull

    Raises
    ------
    ValueError
        if `f_type` not in literal list
        if `year` is definitely invalid
    """
    # validate year parameter
    if len(str(year)) != 4:
        raise ValueError('year not 4-digit')
    if year < 1990:
        raise ValueError('No CRA data prior to 1990')
    if year > pd.Timestamp.now().year:
        raise ValueError('data from the future is not yet available')
    if f_type in ['aggr', 'trans', 'discl'] and year < 1996:
        raise ValueError(f'data for {f_type} not present prior to 1996')

    # create folder
    os.makedirs(path.join('downloads', f_type), exist_ok=True)
    if f_type in ['aggr', 'trans', 'discl']:
        # https://www.ffiec.gov/cra/craflatfiles.htm
        y_stub = '{:02d}'.format(year % 100)
        download(
            f'https://www.ffiec.gov/cra/xls/{y_stub}exp_{f_type}.zip',
            path.join('downloads', f'{y_stub}exp_{f_type}.zip'),
            referrer=__ADCFFL
        )
        return

    if f_type == 'census':
        # https://www.ffiec.gov/censusapp.htm
        # https://www.ffiec.gov/histcensus.htm
        if 1990 <= year < 2008:
            url = f'https://www.ffiec.gov/Census/Census_Flat_Files/census{year}.zip'
        elif year < 2020:
            url = f'https://www.ffiec.gov/Census/Census_Flat_Files/Zip%20Files/CENSUS{year}.zip'
        elif year < 2022:
            url = f'https://www.ffiec.gov/Census/Census_Flat_Files/Zip%20Files/Census{year}.zip'
        else:
            url = f'https://www.ffiec.gov/Census/Census_Flat_Files/CensusFlatFile{year}.zip'

        download(
            url,
            path.join('downloads', path.basename(url)),
            referrer=__CENSUS
        )
        return

    raise ValueError(f'f_type {f_type} not supported')


if __name__ == '__main__':

    # https://www.ffiec.gov/cra/craproducts.htm
    # CRA data are generally released by August of the year following the
    # calendar year of the data.

    now = pd.Timestamp.now()
    cra_year = now.year if now.month > 8 else now.year - 1
    print(f'identified the current max cra year as {cra_year}')

    files = pd.concat([
        pd.DataFrame(
            itertools.product(
                ['aggr', 'trans', 'discl'],
                list(range(1996, cra_year))
            ), columns=['type', 'year']),
        pd.DataFrame(
            itertools.product(['census'], list(range(1990, cra_year))),
            columns=['type', 'year'])
    ], axis=0)

    pb = tqdm(files.iterrows(), total=len(files), desc='downloading cra')
    with ProcessPoolExecutor(3) as p:

        # spin up three processes for downloads
        futures = []
        for _, row in pb:
            futures.append(p.submit(pull_file, row['year'], row['type']))

        for f in as_completed(futures):
            pb.update(1)

        wait(futures)
        print('completed cra download')

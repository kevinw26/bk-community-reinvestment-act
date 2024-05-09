# -*- coding: utf-8 -*-
"""
Created on Wed 8 May 2024 20:01:40
@author: Kevin.Wong
"""
import lzma
import os
import timeit
from glob import glob
from os import path

import pandas as pd
import polars as pl


def polars():
    trans = pl.concat(
        (
            pl.read_csv(lzma.open(i)) for i in
            sorted(glob(path.join('out', 'trans', '*.csv.xz')))
        ),
        how='diagonal'
    )
    gb: pl.DataFrame = trans.group_by('activity_year').agg(
        pl.concat_str(
            [pl.col('agency_code'), pl.col('respondent_id')],
            separator='-'
        ).count().alias('respondent_ct'),
        pl.col('id_rssd').count().alias('rssd_ct')
    ).sort(by=['activity_year'])
    os.makedirs(path.join('out', 'summary'), exist_ok=True)
    gb.write_csv(path.join('out', 'summary', 'transmittal_counts.csv'))


def pandas():
    trans = pd.concat(
        (
            pd.read_csv(i) for i in
            sorted(glob(path.join('out', 'trans', '*.csv.xz')))
        ), axis=0
    )
    trans['_agcdrespid'] = (
            trans['agency_code'].astype(str) + '-'
            + trans['respondent_id'].astype(str)
    )
    gb = trans.groupby('activity_year').agg(
        respondent_ct=('_agcdrespid', 'count'),
        rssd_ct=('id_rssd', 'count')
    ).sort_index()
    os.makedirs(path.join('out', 'summary'), exist_ok=True)
    gb.to_csv(path.join('out', 'summary', 'transmittal_counts.csv'),
              index=True)


if __name__ == '__main__':
    '''
    Apple M2, 16 GB RAM
     - polars elapsed 3.489725375 s (41.21 pc faster!)
     - pandas elapsed 5.936164082 s
    '''
    t_pl = timeit.timeit(polars, number=50)
    print(f'polars elapsed {t_pl}')

    t_pd = timeit.timeit(pandas, number=50)
    print(f'pandas elapsed {t_pd}')

    print(f'speed up by {100 * (1 - (t_pl / t_pd)):.4f}')

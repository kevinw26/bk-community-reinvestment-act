# -*- coding: utf-8 -*-
"""
Created on Fri Apr 26 14:08:50 2024
@author: Kevin.Wong
"""
import numpy as np
import os
import pandas as pd
import pandas.api.types as ptypes
import re
import zipfile as zf

from concurrent.futures import ProcessPoolExecutor, wait, as_completed
from functools import lru_cache
from glob import glob
from io import StringIO
from os import path
from tqdm import tqdm
from typing import Literal, TextIO, Tuple, Union


class MissingSpec(Exception):
    pass


def parse_tableid(record: Union[str, bytes], return_record: bool = False):
    if isinstance(record, bytes):  # decode bytes if necessary
        try:
            record = record.decode('utf-8')
        except UnicodeDecodeError:
            record = record.decode('latin-1')  # fallback for old files

    record = record.strip()  # strip string

    # non-transmittal records have a table id
    m = re.search('^(\w)(\d)-(\d[A-Za-z]?)', record)
    if m:
        table_id = (
            m.group(0).strip().replace('-', '')
            if m.group(3).strip() != '0' else
            m.group(1) + m.group(2)
        ).lower()
        return (table_id, record) if return_record else table_id

    # identify if this is a transmittal record on incipit
    m = re.search(r'(.{10})(\d{1})(\d{4})', record)
    if m:
        # ensure agency code is within valid values
        if not (1 <= int(m.group(2)) <= 4):
            raise ValueError(
                f'input {record} declares invalid agency code {m.group(2)}')

        # ensure year is within valid values [1990, current_year]
        if not (1990 < int(m.group(3)) < pd.Timestamp.now().year):
            raise ValueError(
                f'input {record} declares invalid year {m.group(3)}')

        table_id = ''  # empty table id
        return (table_id, record) if return_record else table_id

    raise ValueError(f'input {record} does not match table id pattern')


@lru_cache(maxsize=100)
def get_spec(f_type: str, table: str):
    p = path.join('specs', 'specs_{}.csv'.format(
        # omit the trailing underscore if there is no table; this should only
        # be the case in f_type == 'trans'
        '_'.join(i for i in [f_type, table] if i != '')
    ))
    if path.exists(p):
        return pd.read_csv(p, index_col=[0])
    raise MissingSpec(f'no spec for {f_type} {table}')


def interpolate_spec(spec, year, record_length):
    """
    If the year column specifications are present, return them. Otherwise, find
    the latest year with the same record length in column specifications and
    use them. If no such year, raise MissingSpec.

    This can cause problems if the record length stays the same BUT the columns
    change length under them. This is not expected behaviour however.
    """
    if year in spec.index:
        return spec.loc[year].dropna().astype(int)

    same_reclen = spec[spec.sum(axis=1) == record_length]
    if len(same_reclen) != 0:
        the_spec = spec.sort_index(ascending=False).iloc[0]
        tqdm.write(
            f'interpolating missing spec {year} with spec at {the_spec.name}')
        return the_spec.dropna().astype(int)

    raise MissingSpec('no matching spec')


def parse_table(
        f: TextIO,
        year: int,
        f_type: Literal['aggr', 'trans', 'discl', 'census'],
        table: str,
        reclen: int,
):
    # cast to year
    if not isinstance(year, int):
        year = int(year)

    # check if the file already exists; skip if so
    output_path = path.join('out', f_type, '{}.csv.xz'.format(
        '-'.join(str(i) for i in [f_type, year, table] if str(i) != '')
    ))
    if path.exists(output_path):
        tqdm.write(f'output file for {f_type} {year} {table} already exists')
        return

    # get the relevant file spec and parse for year
    spec = get_spec(f_type, table)
    if spec.index.duplicated().any():  # warn if duplicated
        tqdm.write(f'duplicate file specs for {f_type} {year} {table} ?')

    # interpolate the spec if necessary
    the_spec = interpolate_spec(spec, year, reclen)

    # do read
    tqdm.write(f'parsing table {table} in {f_type} {year}')
    global df
    df = pd.read_fwf(f, widths=the_spec.dropna().values)
    df.columns = the_spec.index

    # sensibility type checks
    if f_type in ['aggr', 'discl']:
        assert ptypes.is_string_dtype(df['table'])
        assert ptypes.is_numeric_dtype(df['activity_year'])

    if f_type in ['trans']:
        # assert ptypes.is_string_dtype(df['respondent_id'])
        assert ptypes.is_numeric_dtype(df['agency_code'])
        assert ptypes.is_numeric_dtype(df['activity_year'])
        assert ptypes.is_string_dtype(df['respondent_st'])

    # save
    os.makedirs(path.join('out', f_type), exist_ok=True)
    df.to_csv(output_path, index=False)


def parse_file(file_location: Tuple[str, str], year: int,
               f_type: Literal['aggr', 'trans', 'discl', 'census']):
    # nb... f_type == discl with year < 2016 is one big dat file
    # all DAT otherwise are one big dat file

    # reconstruct file handle; buffered readers cannot be serialised
    f = zf.ZipFile(file_location[0]).open(file_location[1], 'r')

    # dynamically get table id and construct List[str] for each
    try:
        tables = {}
        for l in f:
            # skip length 1 and 0 strings
            if len(l) <= 1:
                continue

            # parse the table id and record; add to dictionary
            k, v = parse_tableid(l, return_record=True)
            try:
                tables[k].append(v)
            except KeyError:
                tables[k] = [v]  # init list

    except ValueError as e:
        raise ValueError(
            f'invalid value in {file_location} {year} {f_type}') \
            from e

    # for each table id, parse
    for k, v in tables.items():
        try:
            parse_table(
                StringIO('\n'.join(v)), year, f_type, k,
                reclen=len(v[0])
            )
        except MissingSpec:
            tqdm.write(
                f'skipping missing spec for {f_type} {k} at year {year}')


if __name__ == '__main__':

    # ------------------------------------------------------------------------
    # enumerate the files

    zips = pd.Series(
        sorted(glob(path.join('downloads', '*.zip'))),
        name='path'
    ).to_frame()
    if len(zips) < 1:
        raise ValueError('there are no zip files in the downloads folder')

    zips[['y_stub', 'f_type']] = zips['path'] \
        .apply(path.basename) \
        .str.extract(r'^(\d{2})exp_(\w+)', expand=True)

    _y = zips['y_stub'].pipe(pd.to_numeric)
    zips['year'] = np.where(_y < 90, _y + 2000, _y + 1900)
    zips.sort_values(by=['year', 'f_type'], ascending=True, inplace=True)

    # ------------------------------------------------------------------------
    # try to parse the files

    MULTIPROCESSING = False
    if MULTIPROCESSING:
        with ProcessPoolExecutor(6) as e:
            futures = []
            for _, r in zips.iterrows():
                z = zf.ZipFile(r['path'])
                for sub_z in z.namelist():
                    futures.append(e.submit(
                        parse_file,
                        (r['path'], sub_z), r['year'], r['f_type']
                    ))

            with tqdm(total=len(futures), desc='parsing zips') as pb:
                for f in as_completed(futures):
                    pb.update(1)
                    try:
                        f.result()
                    except Exception as e:
                        [f.cancel() for f in futures]  # cancel all
                        raise e

            wait(futures)

    else:
        for _, r in tqdm(zips.iterrows(), total=len(zips)):
            z = zf.ZipFile(r['path'])
            for sub_z in z.namelist():
                parse_file(
                    (r['path'], sub_z), r['year'], r['f_type']
                )

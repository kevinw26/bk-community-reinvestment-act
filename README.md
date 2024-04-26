# bk-cra

This is a set of scripts to download (if CloudFlare allows it) and parse flat
files from the FFIEC Community Reinvestment Act's public data disclosures. The
files match the pattern `cra\d_.+?\.py` should be executed in alphanumeric
sort order.

This data is kept in fixed-width `.dat` files, making it annoying to work with.
The files are hosted at `https://www.ffiec.gov/cra/craflatfiles.htm`. Because
the file specifications are not easily machine-readable, defined in PDFs, a
substantial of manual work is needed to parse them properly. This not helped by
changes in the file specifications over time (column widths).

## Aggregates
Aggregates are pre-calculated at the county level.

## Transmittal
As with other data products such as pre-2017 HMDA (Home Mortgage Disclosure 
Act), the respondents are identified by `AGENCY_CODE` and `RESPONDENT_ID`. The
agency codes are as follows.

| `AGENCY_CODE`    | Agency               |
| ---------------: | -------------------- |
| 1                | OCC                  |
| 2                | Federal Reserve      |
| 3                | FDIC                 |
| 4                | OTS (abolished 2011) |

Mapping from CRA respondents to standard bank identifiers such as FDIC `CERT`
and Fed `RSSD` is via the transmittal table.

## Geography
The main identifier in aggregates is the county FIPS code. FIPS codes can
change over time as counties expand, contract, split, merge, and rename.
They should be treated as valid only at the same CRA reporting year.

## Authors and acknowledgements
Bryce Bangerter and Kevin Wong

We are indebted to the work of [AC Forrester](
    https://github.com/acforrester/community-reinvestment-act).

The views expressed (if there is any such expression at all) herein do not 
necessarily represent the views of the Office of the Comptroller of the
Currency, the Department of the Treasury, or the United States.

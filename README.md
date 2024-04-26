# bk-cra

This is a set of scripts to download (if CloudFlare allows it) and parse flat
files from the FFIEC Community Reinvestment Act's public data disclosures. The
files match the pattern `src/cra\d_.+?\.py` and should be executed in
alphanumeric sort order.

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

| `AGENCY_CODE`    | Agency                                        |
| ---------------: | --------------------------------------------- |
| 1                | Office of the Comptroller of the Currency     |
| 2                | Federal Reserve                               |
| 3                | Federal Deposit Insurance Corporation         |
| 4                | Office of Thrift Supervision (abolished 2011) |

Mapping from CRA respondents to standard bank identifiers such as FDIC `CERT`
and Fed `RSSD` is via the transmittal table.

The list of CRA reporters can be found on the [FFIEC website](
    https://www.ffiec.gov/cra/reporter.htm). In 2023, the reporters were all
banks regulated by the OCC, Federal Reserve, or FDIC that also had assets in
excess of 1.503 billion $ as of 31 December for the previous two calendar 
years. The reports are filed on or shortly after 1 March of every year.

The banks which are not required to report are called "small banks" for the
purposes of the regulation. This was set by [70 FR 44256](
    https://www.federalregister.gov/d/05-15227/p-3) (2005) at 1 billion $,
adjusting for inflation (CPI). Prior to 2005, reporting was uneven: a "small
bank" was an independent bank with less than 250 million $ in assets or
otherwise affiliated with a holding company that had less than 1 billion $ in
assets. (Both thresholds applying only if they were met for the two preceding
calendar years.) See [66 FR 37602, 37606](
    https://www.federalregister.gov/d/01-18033/p-61) (2001). A final CRA rule 
in 2024, superseding the 1995 rules, kept the inflation-adjusted 2005 
threshold. See [89 FR 6574, 7212](
    https://www.federalregister.gov/d/2023-25797/p-8507) (2024).

## Geography
The main identifier in aggregates is the county FIPS code. FIPS codes can
change over time as counties expand, contract, split, merge, and rename. They
should be treated as valid only at the same CRA reporting year.

## Authors and acknowledgements
Bryce Bangerter and Kevin Wong

We are indebted to the work of [AC Forrester](
    https://github.com/acforrester/community-reinvestment-act).

The views expressed (if there is any such expression at all) herein do not 
necessarily represent the views of the Office of the Comptroller of the
Currency, the Department of the Treasury, or the United States.

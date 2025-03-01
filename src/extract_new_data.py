import nasdaqdatalink
import sqlite3
import datetime
import os
import csv
from datetime import timedelta
from dataflows import (
    Flow,
    PackageWrapper,
    validate,
)
from dataflows import add_metadata, dump_to_path, load, set_type, printer


API_KEY = 'yrCdCJCAzfaEUHHixEJF'
DATA_DIR = os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), 'data')
BTC_CSV_FILE = os.path.join(DATA_DIR, 'bitcoin_data.csv')


def fetch_btc_data(start_date, end_date):
    try:
        data = nasdaqdatalink.get_table(
            'QDL/BCHAIN',
            api_key=API_KEY,
            date={'gte': start_date, 'lte': end_date},
            code='MKPRU',
            paginate=True,
        )
        btc_data = {}
        for _, row in data.iterrows():
            date_str = str(row['date'])
            price = row['value']
            btc_data[date_str] = price
        return btc_data
    except nasdaqdatalink.DataLinkError as e:
        print(f"Error fetching Bitcoin data: {e}")
        return {}


def export_to_csv(file_path, data, header):
    """Exports data to a CSV file."""
    try:
        with open(file_path, mode='w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(header)
            for date, price in data.items():
                csv_writer.writerow([date, price])
        print(f"Data exported successfully to '{file_path}'")
    except Exception as e:
        print(f"Error writing CSV file: {e}")


def filter_out_empty_rows(rows):
    for row in rows:
        if row["Date"]:
            yield row


def filter_date_range(rows, start_date_str):
    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    for row in rows:
        if row["Date"] >= start_date:
            yield row


def rename_resources(package: PackageWrapper):
    package.pkg.descriptor["resources"][0]["name"] = "wti-daily"
    yield package.pkg
    res_iter = iter(package)
    for res in res_iter:
        yield res.it
    yield from package


OIL_PRICES = Flow(
    load(
        load_source="http://www.eia.gov/dnav/pet/hist_xls/RWTCd.xls",
        format="xls",
        sheet=2,
        skip_rows=[1, 2, 3],
        headers=["Date", "Price"],
    ),
    lambda package: rename_resources(package),
    set_type("Date", resources=None, type="date", format="any"),
    validate(resources=['wti-daily']),
    filter_out_empty_rows,
    lambda rows: filter_date_range(rows, str(datetime.date.today() - timedelta(days = 1))),
    dump_to_path(out_path=DATA_DIR),
)


def main():
    today = datetime.date.today()
    yesterday = today - timedelta(days = 1)

    print(f"Current working directory: {os.getcwd()}")

    print('fetching btc data...')
    btc_data = fetch_btc_data(str(yesterday), str(today))

    print('fetching wti data...')
    OIL_PRICES.process()

    print('exporting btc to csv...')
    export_to_csv(BTC_CSV_FILE, btc_data, ['Date', 'Bitcoin Price'])

    print('exporting wti to csv...')

    print('data extraction complete.')


if __name__ == '__main__':
    main()

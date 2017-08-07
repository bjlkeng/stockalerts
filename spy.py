"""

Small script to implement a mechanical investing signal for SPY:
http://boards.fool.com/getting-away-from-the-bear-27035352.aspx

"""

from pandas_datareader import data as pdr_data
import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime


def fetch_data(source):
    """ Get data from

        :param source: one of 'google', 'yahoo'
    """
    today = date.today()
    start_date = today - timedelta(days=365 * 10)
    end_date = today if datetime.now().hour > 17 else today - timedelta(days=1)

    panel_data = pdr_data.DataReader(['SPY'], source,
                                     start_date, end_date)

    return panel_data['Close'].sort_index().copy()


def next_weekday(dt):
    while True:
        dt = dt + timedelta(days=1)
        # Mon = 1, Sun = 7
        if dt.isoweekday() <= 5:

            return dt


def check_dates(data):
    dates = data.index
    expected = dates[0]
    current_year = expected.year
    skipped = 0

    for dt in dates:
        if dt != expected:
            skipped += 1
            expected = next_weekday(expected)
        expected = next_weekday(expected)

        if dt.year != current_year:
            if skipped > 13:
                raise ValueError('%d skipped %d days (expected < 13)' % (current_year, skipped))
            current_year = dt.year
            skipped = 0


def compute_signal(data):
    data = data.copy()
    data['max_99'] = data['SPY'].rolling(window=99, center=False).max()
    data['buy'] = data['max_99'].diff(1).apply(np.sign)

    return data


def signal_to_str(val):
    if val > 0:
        return 'BUY'
    elif val < 0:
        return 'SELL'
    else:
        return 'DO NOTHING'


if __name__ == "__main__":
    data = fetch_data('google')
    check_dates(data)
    gdata = compute_signal(data)
    gdata.columns = ['g' + c for c in gdata.columns]

    data = fetch_data('yahoo')
    check_dates(data)
    ydata = compute_signal(data)
    ydata.columns = ['y' + c for c in ydata.columns]

    data = pd.concat([gdata, ydata], axis=1)
    data['valid'] = ((data['gSPY'] - data['ySPY']).abs() < 0.01).astype(int)

    valid = 'YES' if data['valid'].tail(100).min() == 1 else 'NO'

    print('Date: %s' % data.index[-1])
    print('Close: %s' % data['gSPY'].iloc[-1])
    print('Valid: %s' % valid)
    print('Signal: %s' % signal_to_str(data['gbuy'].iloc[-1]))
    print('')
    print(data[data['gbuy'] != 0][['gSPY', 'gmax_99', 'gbuy']].tail(10))

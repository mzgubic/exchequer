import pandas as pd
import dateutil
from dateutil.rrule import rrule, MONTHLY, DAILY
from datetime import datetime, date, timedelta

# output format
df = pd.DataFrame(columns=['date', 'amount', 'currency', 'category', 'description'])

# get the input file
input_df = pd.read_csv('private_repeated.csv')

# loop over the rows in the dataframe
for i in input_df.index:

    # get row
    row = input_df.loc[i]

    # extract info
    start_date = datetime.strptime(row.start, '%Y-%m-%d').date()
    end_date = datetime.strptime(row.end, '%Y-%m-%d').date()
    total_amount = row.amount
    freq = getattr(dateutil.rrule, row.frequency)

    # prepare dates at which to save the expense
    dates = list(rrule(freq=freq, dtstart=start_date, until=end_date))
    up_to_now = len(df)

    for i, date in enumerate(dates):
        df.loc[up_to_now+i] = [date, total_amount/len(dates), row.currency, row.category, row.description]


print(df)
df.to_csv('repeated.csv', index=False)

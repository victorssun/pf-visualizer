"""
Dashboard to summarily visualize data
- execute commandline iva `streamlit run <script>.py
- use with st.echo() and st.experimental_show() for debugging
"""
import sqlite3
import streamlit as st
import altair as alt
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def fetch_from_db(sql_statement):
    cursor.execute(sql_statement)
    return cursor.fetchall()


class AggregationDate:
    Monthly = 'Monthly'
    Yearly = 'Yearly'


class Month:
    Jan = ['January', '01']
    Feb = ['February', '02']
    Mar = ['March', '03']
    Apr = ['April', '04']
    May = ['May', '05']
    Jun = ['June', '06']
    Jul = ['July', '07']
    Aug = ['August', '08']
    Sep = ['September', '09']
    Oct = ['October', '10']
    Nov = ['November', '11']
    Dec = ['December', '12']
    Months = [Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec]


class Expenses:
    EatingOut = 'eating out'
    Groceries = 'groceries'
    Restaurants = 'restaurants'
    PersonalItems = 'personal items'
    Extra = 'extra'
    Transportation = 'transportation'
    Housing = 'housing'
    Education = 'education'
    Help = 'help'
    List = [EatingOut, Groceries, Restaurants, PersonalItems, Extra, Transportation, Housing, Education, Help]


### MAIN ###
pf_directory = ''

# set up
path_db = '{}monthly_summary.db'.format(pf_directory)
conn = sqlite3.connect(path_db)
cursor = conn.cursor()

### sidebar ###
st.set_page_config('Personal Finance Visualization', 'random', initial_sidebar_state='auto',
                   menu_items={"Get help": None, "Report a bug": None, "About": None})

st.sidebar.write('<br>', unsafe_allow_html=True)
st.sidebar.write('#### Select')

# month or year
col1, col2 = st.sidebar.columns(2)
month_or_year = col1.radio("Aggregation : ", [AggregationDate.Monthly, AggregationDate.Yearly])
date_dt = col2.date_input("Start Date: ", value=pd.to_datetime('2014-03-01'),
                       min_value=pd.to_datetime('2014-03-01'), max_value=pd.to_datetime('today'))
date_dt_start = date_dt.strftime('%Y-%m-%d')

# month
col1, col2 = st.sidebar.columns(2)
month = col1.select_slider('End/Summary Month: ', ['January', 'February', 'March', 'April', 'May', 'June',
                                             'July', 'August', 'September', 'October', 'November', 'December'])

# year
year = col2.select_slider('Year: ', [str(year) for year in range(2014,2022+1)], value=str(2022))

st.sidebar.write("<hr>Dashboard visualization for historical, personal finances. "
                 "Made by <a style='color:LightSkyBlue; text-decoration: none;' href=https://www.victorssun.com/>Victor Sun</a>.", unsafe_allow_html=True)


### main page ####
st.markdown("""<style>footer {visibility: hidden;}</style>""", unsafe_allow_html=True)
st.write('# Personal Finance Visualizer')
if month_or_year == AggregationDate.Yearly:
    st.write('## {} Summary'.format(year))
    start_date = '{}-01-01'.format(year)
    end_date = '{}-12-31'.format(year)
    monthly_summary = fetch_from_db("SELECT * FROM monthly_summary "
                                    "WHERE date BETWEEN '{}' AND '{}'".format(start_date, end_date)
                                    )
else:
    st.write('## {} {} Summary'.format(month, year))

    for m in Month.Months:
        if month == m[0]:
            month_num = m[1]
            break
    
    end_date = '{}-{}-20'.format(year, month_num)
    monthly_summary = fetch_from_db("SELECT * FROM monthly_summary "
                                    "WHERE date = '{}-{}-20'".format(year, month_num)
                                    )

col_names = fetch_from_db("PRAGMA table_info(monthly_summary)")
col_names = [col[1] for col in col_names]
monthly_summary = pd.DataFrame(monthly_summary, columns=col_names)

# metrics
expenses = monthly_summary[Expenses.List].sum().sum()
income = monthly_summary['income'].sum()

col1, col2, col3 = st.columns(3)
col1.metric('', '{:.2f}'.format(income), "Income")
col2.metric('', '{:.2f}'.format(expenses), "-Expenses")

savings = income - expenses
savings_delta = "-Savings" if savings < 0 else "Savings"
col3.metric('', '{:.2f}'.format(savings), savings_delta)

expenses = monthly_summary[Expenses.List].sum()
expenses = expenses.reset_index(level=0)
expenses.columns = ['expense', 'value']
fig = go.Figure(
    data=[go.Pie(
        labels=expenses['expense'],
        values=expenses['value'],
        sort=False
        )
    ])

fig.update_traces(textinfo='label+value')
st.plotly_chart(fig, use_container_width=True)

st.write('### Expenses')
monthly_summary = fetch_from_db("SELECT * FROM monthly_summary "
                                "WHERE date BETWEEN '{}' AND '{}'".format(date_dt_start, end_date))
monthly_summary = pd.DataFrame(monthly_summary, columns=col_names)
monthly_summary['date'] = pd.to_datetime(monthly_summary['date'], format='%Y-%m-%d')

monthly_summary['savings'] = monthly_summary['income']
for expenses in Expenses.List:
    monthly_summary['savings'] = monthly_summary['savings'] - monthly_summary[expenses]

bank = monthly_summary[['date', 'bank']]
if month_or_year == AggregationDate.Yearly:
    monthly_summary = monthly_summary.groupby(monthly_summary['date'].map(lambda x: x.year)).sum()
    monthly_summary = monthly_summary.reset_index(level=0)

fig = px.bar(monthly_summary, x="date", y=Expenses.List)
fig.update_layout(legend=dict(
    yanchor="top",
    y=0.99,
    xanchor="left",
    x=0.01
))
st.plotly_chart(fig, use_container_width=True)

st.write('### Income')
fig = px.bar(monthly_summary, x="date", y='income')
st.plotly_chart(fig, use_container_width=True)

st.write('### Net Worth')
fig = alt.Chart(bank).mark_line().encode(x=alt.X('date', title='Date'), y=alt.Y('bank', title='Net Worth'), tooltip=['date', 'bank']).properties(height=400)
st.altair_chart(fig, use_container_width=True)

st.write('### Savings')
fig = px.bar(monthly_summary, x="date", y='savings')
st.plotly_chart(fig, use_container_width=True)

# st.experimental_show(monthly_summary) #
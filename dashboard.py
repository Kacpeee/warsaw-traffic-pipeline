import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

st.set_page_config(page_title='Warsaw Transit', layout='wide')

DB = 'warsaw_dbt/dev.duckdb'

@st.cache_data(ttl=60)
def q(sql):
    con = duckdb.connect(DB, read_only=True)
    df = con.execute(sql).fetchdf()
    con.close()
    return df

st.title('Warsaw Public Transport')
st.caption('Live vehicle positions matched against the GTFS timetable')

# --- headline numbers -------------------------------------------------
overview = q('''
    select
        (select count(*) from stg_positions)          as positions,
        (select count(*) from int_vehicle_moves)      as moves,
        (select count(*) from int_vehicle_delays)     as matched,
        (select round(median(speed_kmh),1) from int_vehicle_moves)     as med_speed,
        (select round(median(delay_minutes),2) from int_vehicle_delays) as med_delay
''').iloc[0]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric('Positions collected', f"{overview.positions:,}")
c2.metric('Movements', f"{overview.moves:,}")
c3.metric('Matched to schedule', f"{overview.matched:,}")
c4.metric('Median speed', f"{overview.med_speed} km/h")
c5.metric('Median delay', f"{overview.med_delay} min")

tab1, tab2, tab3 = st.tabs(['Speed by hour', 'Punctuality', 'Worst stops'])

# --- speed -------------------------------------------------------------
with tab1:
    df = q('''
        select hour_of_day,
               sum(measurements) as n,
               round(sum(avg_speed_kmh*measurements)/sum(measurements),1) as avg_speed,
               round(sum(pct_crawling*measurements)/sum(measurements),1)  as pct_crawling
        from mart_speed_by_hour group by 1 order by 1
    ''')
    if df.empty:
        st.info('No data yet.')
    else:
        fig = px.bar(df, x='hour_of_day', y='avg_speed',
                     labels={'hour_of_day':'Hour of day','avg_speed':'Average speed (km/h)'},
                     title='Average speed by hour')
        st.plotly_chart(fig, width='stretch')

        fig2 = px.line(df, x='hour_of_day', y='pct_crawling', markers=True,
                       labels={'hour_of_day':'Hour of day','pct_crawling':'% of time below 5 km/h'},
                       title='Congestion indicator')
        st.plotly_chart(fig2, width='stretch')
        st.dataframe(df, width='stretch', hide_index=True)

# --- punctuality --------------------------------------------------------
with tab2:
    col_a, col_b = st.columns(2)
    with col_a:
        d1 = q('select * from mart_punctuality_by_hour order by hour_of_day')
        if not d1.empty:
            fig = px.bar(d1, x='hour_of_day', y='avg_delay_min',
                         labels={'hour_of_day':'Hour','avg_delay_min':'Average delay (min)'},
                         title='Delay by hour of day')
            st.plotly_chart(fig, width='stretch')
    with col_b:
        d2 = q('select * from mart_line_punctuality order by avg_delay_min desc limit 20')
        if not d2.empty:
            fig = px.bar(d2, x='avg_delay_min', y='line', orientation='h',
                         labels={'avg_delay_min':'Average delay (min)','line':'Line'},
                         title='Least punctual lines')
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, width='stretch')
    st.dataframe(q('select * from mart_line_punctuality'), width='stretch', hide_index=True)

# --- worst stops --------------------------------------------------------
with tab3:
    stops = q('select * from mart_worst_stops')
    if stops.empty:
        st.info('Not enough measurements per stop yet.')
    else:
        fig = px.scatter_map(stops,
            lat='stop_lat', lon='stop_lon',
            color='avg_delay_min', size='measurements',
            hover_name='stop_name',
            hover_data={'avg_delay_min':True,'pct_late':True,'lines_served':True,
                        'stop_lat':False,'stop_lon':False},
            color_continuous_scale='RdYlGn_r', zoom=10, height=600,
            map_style='carto-positron',
            title='Average delay per stop')
        st.plotly_chart(fig, width='stretch')
        st.dataframe(stops, width='stretch', hide_index=True)

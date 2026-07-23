import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

TEMPLATE = 'plotly_dark'
ACCENT = '#4C9BE8'

def style(fig, height=380):
    fig.update_layout(
        template=TEMPLATE, height=height, coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=13), title_font_size=16,
        xaxis=dict(gridcolor='rgba(255,255,255,0.08)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.08)'),
    )
    return fig

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

# --- filters ------------------------------------------------------------
with st.sidebar:
    st.header('Filters')

    modes = q("select distinct vehicle_type from stg_positions order by 1")
    mode_labels = {1: 'Bus', 2: 'Tram'}
    chosen_modes = st.multiselect(
        'Vehicle type',
        options=[mode_labels.get(m, str(m)) for m in modes['vehicle_type']],
        default=[mode_labels.get(m, str(m)) for m in modes['vehicle_type']],
    )

    min_obs = st.slider(
        'Minimum observations', min_value=5, max_value=200, value=10, step=5,
        help='Drop lines or stops with too few measurements to be meaningful.',
    )

    hours = st.slider(
        'Hour of day', min_value=0, max_value=23, value=(0, 23),
        help='Restrict time-based views to a window of the day.',
    )

    st.divider()
    st.caption(
        'Filters apply to the aggregate views. Underlying models are rebuilt '
        'hourly by Airflow.'
    )

MODE_IDS = [k for k, v in mode_labels.items() if v in chosen_modes] or [1, 2]

# --- headline numbers -------------------------------------------------
overview = q(f'''
    select
        (select count(*) from stg_positions
         where vehicle_type in ({','.join(map(str, MODE_IDS))}))  as positions,
        (select count(*) from int_vehicle_moves)      as moves,
        (select count(*) from int_vehicle_delays)     as matched,
        (select round(median(speed_kmh),1) from int_vehicle_moves)     as med_speed,
        (select round(median(delay_minutes),2) from int_vehicle_delays) as med_delay
''').iloc[0]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric('Positions collected', f"{int(overview.positions):,}")
c2.metric('Movements', f"{int(overview.moves):,}")
c3.metric('Matched to schedule', f"{int(overview.matched):,}")
c4.metric('Median speed', f"{overview.med_speed} km/h")
c5.metric('Median delay', f"{overview.med_delay} min")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ['Speed by hour', 'Punctuality', 'Worst stops', 'Regularity', 'Segments', 'Maps'])

# --- speed -------------------------------------------------------------
with tab1:
    df = q(f'''
        select hour_of_day,
               sum(measurements) as n,
               round(sum(avg_speed_kmh*measurements)/sum(measurements),1) as avg_speed,
               round(sum(pct_crawling*measurements)/sum(measurements),1)  as pct_crawling
        from mart_speed_by_hour
        where measurements >= {min_obs}
          and hour_of_day between {hours[0]} and {hours[1]}
        group by 1 order by 1
    ''')
    if df.empty:
        st.info('No data yet.')
    else:
        df['hour_of_day'] = df['hour_of_day'].astype(str)
        fig = px.bar(df, x='hour_of_day', y='avg_speed', color_discrete_sequence=[ACCENT], text_auto='.1f',
                     labels={'hour_of_day':'Hour of day','avg_speed':'Average speed (km/h)'},
                     title='Average speed by hour')
        st.plotly_chart(style(fig), width='stretch')

        fig2 = px.line(df, x='hour_of_day', y='pct_crawling', markers=True, color_discrete_sequence=[ACCENT],
                       labels={'hour_of_day':'Hour of day','pct_crawling':'% of time below 5 km/h'},
                       title='Congestion indicator')
        st.plotly_chart(style(fig2), width='stretch')
        st.dataframe(df, width='stretch', hide_index=True)

# --- punctuality --------------------------------------------------------
with tab2:
    col_a, col_b = st.columns(2)
    with col_a:
        d1 = q(f'select * from mart_punctuality_by_hour where measurements >= {min_obs} and hour_of_day between {hours[0]} and {hours[1]} order by hour_of_day')
        if not d1.empty:
            d1['hour_of_day'] = d1['hour_of_day'].astype(str)
            fig = px.bar(d1, x='hour_of_day', y='avg_delay_min', color='avg_delay_min', color_continuous_scale='RdYlGn_r', text_auto='.1f',
                         labels={'hour_of_day':'Hour','avg_delay_min':'Average delay (min)'},
                         title='Delay by hour of day')
            st.plotly_chart(style(fig), width='stretch')
    with col_b:
        d2 = q(f'select * from mart_line_punctuality where measurements >= {min_obs} order by avg_delay_min desc limit 10')
        if not d2.empty:
            d2['line'] = d2['line'].astype(str)
            fig = px.bar(d2, x='avg_delay_min', y='line', orientation='h', color='avg_delay_min', color_continuous_scale='RdYlGn_r', text_auto='.1f',
                         labels={'avg_delay_min':'Average delay (min)','line':'Line'},
                         title='Least punctual lines')
            fig.update_traces(textposition='outside')
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(style(fig), width='stretch')
    st.dataframe(q(f'select * from mart_line_punctuality where measurements >= {min_obs}'), width='stretch', hide_index=True)

# --- worst stops --------------------------------------------------------
with tab3:
    stops = q(f'select * from mart_worst_stops where measurements >= {min_obs}')
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
        st.plotly_chart(style(fig, 600), width='stretch')
        st.dataframe(stops, width='stretch', hide_index=True)


# --- regularity ---------------------------------------------------------
with tab4:
    st.caption(
        "Headway is the gap between consecutive vehicles of the same line at a stop. "
        "The irregularity index is the standard deviation divided by the mean: "
        "below 0.5 means a predictable rhythm, above 1.0 means the wait is a lottery. "
        "Only frequent services (average headway under 20 min) are shown."
    )

    reg = q(f'select * from mart_line_regularity where observations >= {min_obs}')
    if reg.empty:
        st.info('Not enough data yet.')
    else:
        c1, c2 = st.columns(2)
        with c1:
            worst = reg.head(15).copy()
            worst['line'] = worst['line'].astype(str)
            fig = px.bar(worst, x='irregularity_index', y='line', orientation='h',
                         color='irregularity_index', color_continuous_scale='RdYlGn_r',
                         text_auto='.2f',
                         labels={'irregularity_index': 'Irregularity index', 'line': 'Line'},
                         title='Least predictable lines')
            fig.update_traces(textposition='outside')
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(style(fig, 480), width='stretch')

        with c2:
            bunch = reg.nlargest(15, 'pct_bunched').copy()
            bunch['line'] = bunch['line'].astype(str)
            fig = px.bar(bunch, x='pct_bunched', y='line', orientation='h',
                         color='pct_bunched', color_continuous_scale='Reds',
                         text_auto='.1f',
                         labels={'pct_bunched': '% of arrivals bunched', 'line': 'Line'},
                         title='Most bunching (vehicles arriving together)')
            fig.update_traces(textposition='outside')
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(style(fig, 480), width='stretch')

        fig = px.scatter(reg, x='avg_headway_min', y='irregularity_index',
                         size='observations', hover_name='line',
                         color='pct_bunched', color_continuous_scale='Reds',
                         labels={'avg_headway_min': 'Average headway (min)',
                                 'irregularity_index': 'Irregularity index',
                                 'pct_bunched': '% bunched'},
                         title='Frequency vs predictability')
        st.plotly_chart(style(fig, 420), width='stretch')

        st.dataframe(reg, width='stretch', hide_index=True)


# --- route segments -----------------------------------------------------
with tab5:
    st.caption(
        "Where time is actually lost: each row is a segment between two "
        "consecutive stops, comparing observed travel time against the "
        "timetable. A segment consistently over schedule points to a planning "
        "gap or a recurring bottleneck rather than a one-off delay."
    )

    seg = q(f'select * from mart_slowest_segments where observations >= {min_obs}')
    if seg.empty:
        st.info('Not enough data yet.')
    else:
        seg['route'] = seg['from_stop'].str.slice(0, 18) + ' \u2192 ' + seg['to_stop'].str.slice(0, 18)
        seg['label'] = seg['line'].astype(str) + ':  ' + seg['route']

        top = seg.head(10).sort_values('avg_lost_min')
        fig = px.bar(top, x='avg_lost_min', y='label', orientation='h',
                     color='avg_lost_min', color_continuous_scale='Reds',
                     text_auto='.1f',
                     labels={'avg_lost_min': 'Minutes lost per run', 'label': ''},
                     title='Biggest bottlenecks')
        fig.update_traces(textposition='outside', cliponaxis=False)
        st.plotly_chart(style(fig, 400), width='stretch')

        st.markdown('**Worst segments in detail**')
        detail = seg.head(20)[
            ['line', 'from_stop', 'to_stop', 'avg_scheduled_min',
             'avg_actual_min', 'avg_lost_min', 'observations']
        ].rename(columns={
            'line': 'Line',
            'from_stop': 'From',
            'to_stop': 'To',
            'avg_scheduled_min': 'Scheduled (min)',
            'avg_actual_min': 'Actual (min)',
            'avg_lost_min': 'Lost (min)',
            'observations': 'Runs',
        })
        st.dataframe(detail, width='stretch', hide_index=True)


# --- maps ---------------------------------------------------------------
with tab6:
    view = st.radio('View', ['Speed grid', 'Movement over time'],
                    horizontal=True, label_visibility='collapsed')

    if view == 'Speed grid':
        st.caption(
            'Average speed aggregated onto a ~300 m grid. Point-level speeds are '
            'too noisy to read directly; grid cells expose the corridors where '
            'traffic consistently slows down.'
        )
        grid = q(f'select * from mart_speed_grid where observations >= {min_obs}')
        if grid.empty:
            st.info('Not enough data yet.')
        else:
            fig = px.scatter_map(
                grid, lat='cell_lat', lon='cell_lon',
                color='avg_speed_kmh', size='observations',
                color_continuous_scale='RdYlGn', range_color=[5, 35],
                hover_data={'avg_speed_kmh': True, 'pct_crawling': True,
                            'observations': True, 'cell_lat': False,
                            'cell_lon': False},
                zoom=10.6, center={'lat': 52.23, 'lon': 21.01},
                height=900, map_style='carto-darkmatter',
                labels={'avg_speed_kmh': 'Avg speed (km/h)'},
            )
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, width='stretch')
            st.caption(f'{len(grid):,} cells · red = slow, green = free-flowing')

    else:
        st.caption(
            'Vehicle positions sampled every 15 minutes. Press play to watch the '
            'network fill up in the morning and empty out overnight.'
        )
        frames = q('select * from mart_animation_frames order by frame_time')
        if frames.empty:
            st.info('Not enough data yet.')
        else:
            fig = px.scatter_map(
                frames, lat='lat', lon='lon',
                color='mode', animation_frame='frame_label',
                hover_name='line',
                color_discrete_map={'Bus': '#4C9BE8', 'Tram': '#E8804C'},
                zoom=10.6, center={'lat': 52.23, 'lon': 21.01},
                height=900, map_style='carto-darkmatter',
            )
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            fig.update_traces(marker=dict(size=9))
            st.plotly_chart(fig, width='stretch')
            st.caption(
                f'{len(frames):,} positions across '
                f'{frames["frame_label"].nunique()} frames'
            )

import pandas as pd
import altair as alt

CHART_WIDTH = 850
CHART_HEIGHT = 400
downsample_skip_days = 7

def resample_and_add_zeros(df):
    task_id = df.iloc[0, 0]
    data = {"task_id": [task_id], "num_fte": [0], "weeks_work": [0]}
    before = pd.DataFrame(
        data, index=[df.index[0] - pd.DateOffset(downsample_skip_days)])
    after = pd.DataFrame(
        data, index=[df.index[1] + pd.DateOffset(downsample_skip_days)])
    df = pd.concat([before, df, after])
    return df.resample('D').fillna(method='pad')

gd = pd.read_csv("gantt.csv", parse_dates=["start", "end"])

gd["end"] = gd["end"] - pd.DateOffset(1)
gd["num_fte"] = gd["weeks_work"]*7/(gd["end"] - gd["start"]).dt.days
gd['task_id'] = range(1, len(gd)+1)
# gd["task"] = gd['task_id'].map('{:02}'.format) + " " + gd["task"]
starts = gd[['start', 'task_id']].rename(columns={'start': 'date'})
ends = gd[['end', 'task_id']].rename(columns={'end': 'date'})
start_end = pd.concat([starts, ends]).set_index('date')

cols_retain = ['start', 'task_id', "num_fte", "weeks_work"]
starts = gd[cols_retain].rename(columns={'start': 'date'})

cols_retain = ['end', 'task_id', "num_fte", "weeks_work"]
ends = gd[cols_retain].rename(columns={'end': 'date'})
start_end = pd.concat([starts, ends]).set_index('date')

fact_table = start_end.groupby("task_id").apply(resample_and_add_zeros)
del fact_table["task_id"]
fact_table = fact_table.reset_index()
fact_table = fact_table.rename(columns={'level_1': 'date'})

merge_gd = gd.copy()
del merge_gd["weeks_work"]
del merge_gd["num_fte"]

final = fact_table.merge(merge_gd, right_on='task_id', left_on='task_id', how='left')

# Downsample
f1 = final["date"].dt.day % downsample_skip_days == 0
final = final[f1]

dead = pd.read_csv("deadlines.csv")

# Set up common x axis
dt1 = alt.DateTime(year=2024, month=1, date=14)
dt2 = alt.DateTime(year=2024, month=5)
x_scale = alt.Scale(domain=(dt1, dt2))

tt = [
    alt.Tooltip("Assignment")
]

# dtt = alt.Tooltip("dead_desc")
# dtt2 = alt.Tooltip("Type")
no_axis_title = axis = alt.Axis(title="")

# for v in range(len(gd["task"])):
#     gd["task"][v] = gd["task"][v][1:]

alt_dead = alt.Chart(dead).mark_text(align="center", baseline="middle", size=32).encode(
    y=alt.Y('task_o:N'),
    x=alt.X('start:T', scale=x_scale, axis=alt.Axis(format="%a %-m/%-d", values=[
        alt.DateTime(year=2024, month=1, date=19), alt.DateTime(year=2024, month=1, date=26), alt.DateTime(year=2024, month=2, date=2),
        alt.DateTime(year=2024, month=2, date=9), alt.DateTime(year=2024, month=2, date=16),
        alt.DateTime(year=2024, month=2, date=23), alt.DateTime(year=2024, month=3, date=1),
        alt.DateTime(year=2024, month=3, date=8), alt.DateTime(year=2024, month=3, date=15),
        alt.DateTime(year=2024, month=3, date=22), alt.DateTime(year=2024, month=3, date=29),
        alt.DateTime(year=2024, month=4, date=5), alt.DateTime(year=2024, month=4, date=12),
        alt.DateTime(year=2024, month=4, date=19), alt.DateTime(year=2024, month=4, date=26),
    ])),
    text=alt.Text('mark'),
    tooltip="dead_desc"
)

cutoff = pd.read_csv("shading.csv", parse_dates=["start", "end"])

areas = alt.Chart(cutoff.reset_index()).mark_rect(
    opacity=0.05
).encode(
    x=alt.X('start', scale=x_scale, axis=no_axis_title),
    x2='end',
    y=alt.value(0),  # pixels from top
    y2=alt.value(CHART_HEIGHT),  # pixels from top
    # color='gray'
)

y_scale = alt.Scale(padding=0.3)

cat_names = ['Pitch Assignment', 'Project Proposal', 'Project Design', 'Peer Review', 'Milestone 1', 'Milestone 2', 'Final']
# print(list(gd['task']))
alt_gantt_1 = alt.\
    Chart(gd).\
    mark_bar().\
    encode(
        x=alt.X('start', scale=x_scale, axis=no_axis_title),
        x2='end',
        y=alt.Y('task', scale=y_scale, axis=no_axis_title, sort=cat_names),
        color=alt.Color('Category', legend=alt.Legend(orient="right")),
        # opacity=alt.Opacity('num_fte', legend=None),
        tooltip=tt
    )\
    .properties(width=CHART_WIDTH, height=CHART_HEIGHT)

alt_gantt_2 = alt_gantt_1.mark_text(dx=4, dy=0, align='left', baseline='middle', fontSize=14)\
    .encode(
    text='desc'
)
alt_gantt_2.encoding.color = alt.Undefined
alt_gantt_2.encoding.opacity = alt.Undefined
alt_gantt_2.encoding.tooltip = tt

alt_gantt_layered = areas + alt_gantt_1 + alt_gantt_2 + alt_dead
alt_gantt_layered = alt_gantt_layered.configure_axis(
        labelFontSize=11.5,
        titleFontSize=11.5,
    ).configure_legend(
        titleFontSize=16,
        labelFontSize=14
    )

# alt_util = alt.Chart(final).mark_area(interpolate="monotone").encode(
#     x=alt.X('date', scale=x_scale, axis=no_axis_title),
#     y=alt.Y('sum(num_fte)',
#             axis=alt.Axis(title="Sum of FTE required")),
#     color='Type'
# ).properties(width=CHART_WIDTH, height=100)

# alt_cat = alt_util.mark_line().encode(
#     y=alt.Y('sum(num_fte)', axis=alt.Axis(title="FTE required")),
#     color='Category'
# )

# import numpy as np
# gd['priority'] = gd['priority'] + np.random.uniform(-1, 1, len(gd))
# gd['weeks_work'] = gd['weeks_work'] + np.random.uniform(-1, 1, len(gd))

# alt_work = alt.Chart(gd).mark_point().encode(
#     x=alt.X('weeks_work', axis=alt.Axis(title="Weeks of work for task")),
#     y=alt.X('priority', axis=alt.Axis(title="Task value/priority")),
#     tooltip='desc',
#     color=alt.Color('Type', legend=None)
# ).properties(width=CHART_WIDTH, height=500)

# alt_work_text = alt_work.mark_text(align="left", baseline="middle", size=10, dx=5, dy=-5).encode(
#     text='task'
# )

# alt_work_layered = alt_work + alt_work_text

# vconcat = (alt_gantt_layered & alt_util & alt_cat).resolve_scale("independent")

# final_chart = alt.hconcat(vconcat, alt_work_layered)
alt_gantt_layered.save("index.html")

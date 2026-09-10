
import streamlit as st
import pandas as pd
import numpy as np
import joblib, json
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "seoul-metro-2015.logs.csv"
MODEL = ROOT / "models" / "crowd_forecast_rf.joblib"
METRICS = ROOT / "models" / "metrics.json"

st.set_page_config(page_title="MetroFlow Seoul", page_icon="🚇", layout="wide")

st.markdown("""
<style>
.main-title{font-size:36px;font-weight:850;margin-bottom:0}
.subtitle{color:#64748b;font-size:15px}
.kpi{padding:16px 18px;border-radius:14px;background:linear-gradient(135deg,#eef2ff,#f8fafc);border:1px solid #e2e8f0}
.section{font-size:23px;font-weight:800;margin:8px 0 14px}
.small-note{color:#64748b;font-size:13px}
</style>
""", unsafe_allow_html=True)

USERS = {"admin":"admin123", "operator":"operator123"}
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown('<div class="main-title">🚇 MetroFlow Seoul</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">AI-powered metro crowd intelligence & scheduling support</div>', unsafe_allow_html=True)
    st.divider()
    c1,c2,c3=st.columns([1,1,1])
    with c2:
        st.subheader("Operator Login")
        u=st.text_input("Username")
        p=st.text_input("Password", type="password")
        if st.button("Sign in", use_container_width=True):
            if USERS.get(u)==p:
                st.session_state.auth=True
                st.session_state.user=u
                st.rerun()
            else:
                st.error("Invalid username or password.")
    st.caption("Demo accounts: admin / admin123 • operator / operator123")
    st.stop()

@st.cache_data(show_spinner="Loading the supplied Seoul Metro dataset...")
def load_data():
    cols=["timestamp","station_code","people_in","people_out"]
    x=pd.read_csv(DATA, usecols=cols)
    x["timestamp"]=pd.to_datetime(x["timestamp"], utc=True).dt.tz_convert("Asia/Seoul")
    x["date"]=x["timestamp"].dt.date
    x["hour"]=x["timestamp"].dt.hour
    x["day_name"]=x["timestamp"].dt.day_name()
    x["day_of_week"]=x["timestamp"].dt.dayofweek
    x["month"]=x["timestamp"].dt.month
    x["dayofyear"]=x["timestamp"].dt.dayofyear
    x["weekofyear"]=x["timestamp"].dt.isocalendar().week.astype(int)
    x["total_flow"]=x["people_in"]+x["people_out"]
    x["line"]=x["station_code"].astype(str).str[0].map({str(i):f"Line {i}" for i in range(1,9)}).fillna("Other")
    return x

@st.cache_resource(show_spinner="Loading trained AI model...")
def load_model():
    return joblib.load(MODEL)

df=load_data()
model=load_model()
metrics=json.loads(METRICS.read_text())

st.markdown('<div class="main-title">🚇 MetroFlow Seoul</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Real Seoul Metro passenger-flow intelligence • Supplied 2015 dataset</div>', unsafe_allow_html=True)

with st.sidebar:
    st.success(f"Signed in as **{st.session_state.get('user','operator').title()}**")
    if st.button("Logout"):
        st.session_state.auth=False
        st.rerun()
    st.divider()
    st.subheader("Dashboard Filters")
    selected_line=st.selectbox("Metro line", ["All"]+sorted(df.line.unique()))
    fdf=df if selected_line=="All" else df[df.line==selected_line]
    stations=sorted(fdf.station_code.unique())
    selected_station=st.selectbox("Station code", ["All"]+stations)
    if selected_station!="All":
        fdf=fdf[fdf.station_code==selected_station]
    date_min=df.date.min(); date_max=df.date.max()
    selected_date=st.date_input("Analysis date", value=date_max, min_value=date_min, max_value=date_max)
    st.caption(f"{len(df):,} records • {df.station_code.nunique()} station codes")

total_in=int(fdf.people_in.sum()); total_out=int(fdf.people_out.sum())
peak_hour=int(fdf.groupby("hour").total_flow.sum().idxmax()) if len(fdf) else 0
peak_flow=int(fdf.groupby("hour").total_flow.sum().max()) if len(fdf) else 0
active_days=fdf.date.nunique()

c1,c2,c3,c4=st.columns(4)
for c,title,val in [
    (c1,"Passenger entries",f"{total_in:,}"),
    (c2,"Passenger exits",f"{total_out:,}"),
    (c3,"Peak hour",f"{peak_hour:02d}:00"),
    (c4,"Active days",f"{active_days:,}")
]:
    c.markdown(f'<div class="kpi"><b>{title}</b><br><span style="font-size:27px;font-weight:800">{val}</span></div>', unsafe_allow_html=True)

tab1,tab2,tab3,tab4=st.tabs(["📊 Crowd Monitor","🤖 AI Forecast","🚆 Schedule Planner","📋 Traffic Report"])

with tab1:
    st.markdown('<div class="section">Passenger Flow Monitoring</div>', unsafe_allow_html=True)
    daily=fdf.groupby("date",as_index=False)[["people_in","people_out","total_flow"]].sum()
    hourly=fdf[fdf.date==selected_date].groupby("hour",as_index=False)[["people_in","people_out","total_flow"]].sum()

    a,b=st.columns(2)
    with a:
        st.subheader("Daily passenger trend")
        if len(daily):
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=daily.date,y=daily.people_in,name="Entries",mode="lines"))
            fig.add_trace(go.Scatter(x=daily.date,y=daily.people_out,name="Exits",mode="lines"))
            fig.update_layout(height=360,margin=dict(l=10,r=10,t=20,b=10),xaxis_title="Date",yaxis_title="Passengers",legend_title="")
            st.plotly_chart(fig,use_container_width=True)
    with b:
        st.subheader(f"Hourly passenger flow • {selected_date}")
        if len(hourly):
            fig=px.line(hourly,x="hour",y=["people_in","people_out"],markers=True,
                        labels={"value":"Passengers","hour":"Hour","variable":"Flow"})
            fig.update_layout(height=360,margin=dict(l=10,r=10,t=20,b=10),legend_title="")
            st.plotly_chart(fig,use_container_width=True)
        else:
            st.info("No passenger records for this date/filter.")

    st.subheader("Top 10 busiest station codes")
    top=fdf.groupby("station_code",as_index=False)["total_flow"].sum().sort_values("total_flow",ascending=False).head(10)
    fig=px.bar(top,x="station_code",y="total_flow",text_auto=".3s",
               labels={"station_code":"Station code","total_flow":"Total passenger flow"})
    fig.update_layout(height=390,margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(fig,use_container_width=True)

    st.subheader("Peak-hour profile")
    profile=fdf.groupby("hour",as_index=False)["total_flow"].sum()
    fig=px.bar(profile,x="hour",y="total_flow",text_auto=".3s",
               labels={"hour":"Hour","total_flow":"Passenger flow"})
    fig.update_layout(height=350,margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(fig,use_container_width=True)

    st.caption("Station names are not present in the supplied log file, so the dashboard uses station_code rather than inventing station names.")

with tab2:
    st.markdown('<div class="section">AI Crowd & Demand Forecast</div>', unsafe_allow_html=True)
    st.write("Random Forest regression trained on the supplied Seoul Metro passenger-flow records.")
    st.info("Prediction target: total passenger flow = people_in + people_out.")
    a,b,c=st.columns(3)
    a.metric("MAE",f"{metrics['mae']:,.1f}")
    b.metric("RMSE",f"{metrics['rmse']:,.1f}")
    c.metric("R²",f"{metrics['r2']:.3f}")

    station_for_pred=st.selectbox("Prediction station code",sorted(df.station_code.unique()),key="pred_station")
    pred_date=st.date_input("Prediction date",value=date_max,key="pred_date")
    pred_hour=st.slider("Prediction hour",5,23,18)
    ts=pd.Timestamp(pred_date)
    row=pd.DataFrame([{"station_code":station_for_pred,"hour":pred_hour,
                       "day_of_week":ts.dayofweek,"month":ts.month,
                       "dayofyear":ts.dayofyear,"weekofyear":int(ts.isocalendar().week)}])
    pred=float(model.predict(row)[0])
    st.metric("Predicted passenger flow",f"{pred:,.0f}")
    if pred>3000: st.error("High crowd risk — consider increased train frequency.")
    elif pred>1800: st.warning("Moderate crowd risk — monitor station closely.")
    else: st.success("Lower crowd level based on model prediction.")

    st.subheader("Actual vs predicted flow — selected station")
    hist=df[df.station_code==station_for_pred].groupby("date",as_index=False).agg(
        actual_flow=("total_flow","sum"),hour=("hour","mean"))
    if len(hist):
        sample=hist.tail(30).copy()
        sample["predicted_flow"]=[
            float(model.predict(pd.DataFrame([{
                "station_code":station_for_pred,"hour":int(r.hour),
                "day_of_week":pd.Timestamp(r.date).dayofweek,
                "month":pd.Timestamp(r.date).month,
                "dayofyear":pd.Timestamp(r.date).dayofyear,
                "weekofyear":int(pd.Timestamp(r.date).isocalendar().week)
            }]))[0]) for _,r in sample.iterrows()]
        ]
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=sample.date,y=sample.actual_flow,name="Actual",mode="lines+markers"))
        fig.add_trace(go.Scatter(x=sample.date,y=sample.predicted_flow,name="Predicted",mode="lines+markers"))
        fig.update_layout(height=380,margin=dict(l=10,r=10,t=20,b=10),xaxis_title="Date",yaxis_title="Passenger flow")
        st.plotly_chart(fig,use_container_width=True)

with tab3:
    st.markdown('<div class="section">Train Frequency & Schedule Planning</div>', unsafe_allow_html=True)
    st.warning("The supplied passenger log has timestamps and passenger counts, but no official train arrival/departure timetable. MetroFlow therefore does not fabricate train timings. This module provides demand-based planning recommendations.")
    station=st.selectbox("Station",sorted(df.station_code.unique()),key="sched_station")
    hr=st.slider("Planning hour",5,23,18,key="sched_hour")
    ts=pd.Timestamp(selected_date)
    inp=pd.DataFrame([{"station_code":station,"hour":hr,"day_of_week":ts.dayofweek,
                       "month":ts.month,"dayofyear":ts.dayofyear,
                       "weekofyear":int(ts.isocalendar().week)}])
    demand=float(model.predict(inp)[0])
    if demand>=3500: headway=4
    elif demand>=2500: headway=6
    elif demand>=1500: headway=8
    else: headway=10
    a,b,c=st.columns(3)
    a.metric("Forecast demand",f"{demand:,.0f}")
    b.metric("Recommended headway",f"{headway} min")
    c.metric("Recommended trains / hour",f"{60/headway:.1f}")

    st.subheader("Demand by hour")
    station_hour=df[df.station_code==station].groupby("hour",as_index=False)["total_flow"].sum()
    fig=px.line(station_hour,x="hour",y="total_flow",markers=True,
                labels={"hour":"Hour","total_flow":"Observed passenger flow"})
    fig.add_hline(y=demand,line_dash="dash",annotation_text="Current forecast")
    fig.update_layout(height=370,margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(fig,use_container_width=True)

    obs=station_hour[station_hour.total_flow>0]
    if len(obs):
        st.write(f"Observed passenger activity for station code **{station}** is approximately **{int(obs.hour.min()):02d}:00–{int(obs.hour.max()):02d}:00** in the supplied data.")
    st.caption("Planning logic: higher predicted demand → shorter headway → more trains per hour. This is an AI planning recommendation, not an official Seoul timetable.")

with tab4:
    st.markdown('<div class="section">Traffic Analysis Report</div>', unsafe_allow_html=True)
    report=fdf.groupby("hour",as_index=False).agg(entries=("people_in","sum"),exits=("people_out","sum"),total_flow=("total_flow","sum"))
    report["crowd_level"]=pd.cut(report.total_flow,[-1,100000,250000,500000,np.inf],labels=["Low","Moderate","High","Very High"])
    st.dataframe(report,use_container_width=True)
    csv=report.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download traffic report CSV",csv,"metroflow_traffic_report.csv","text/csv")

    st.subheader("Traffic intensity by hour")
    fig=px.bar(report,x="hour",y="total_flow",color="crowd_level",text_auto=".3s",
               labels={"hour":"Hour","total_flow":"Passenger flow","crowd_level":"Crowd level"})
    fig.update_layout(height=390,margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(fig,use_container_width=True)

    st.subheader("Peak-hour ranking")
    st.dataframe(report.sort_values("total_flow",ascending=False).head(10),use_container_width=True)

st.divider()
st.caption("MetroFlow Seoul • Milestone 1 & 2 prototype • Uses the actual passenger-flow dataset supplied for this project.")

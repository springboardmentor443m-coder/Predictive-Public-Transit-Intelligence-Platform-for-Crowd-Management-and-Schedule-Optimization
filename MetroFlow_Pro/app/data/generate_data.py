from pathlib import Path
import numpy as np, pandas as pd
D=Path(__file__).resolve().parent
STATIONS=[("S01","Taipei Main","Blue",14000),("S02","Ximen","Blue",9000),("S03","Zhongxiao Fuxing","Brown",8500),("S04","Daan","Brown",6500),("S05","Dongmen","Red",6200),("S06","Yuanshan","Red",4800),("S07","Shilin","Red",6000),("S08","Beitou","Red",5100),("S09","Nangang","Blue",7200),("S10","Banqiao","Blue",8000),("S11","Guting","Green",5200),("S12","Gongguan","Green",5800),("S13","Songjiang Nanjing","Orange",5700),("S14","Zhongshan","Red",7300),("S15","Shandao Temple","Blue",3900),("S16","Longshan Temple","Blue",6100),("S17","Jiangzicui","Blue",4900),("S18","Xinpu","Blue",5600),("S19","Kunyang","Blue",4200),("S20","Houshanpi","Blue",3600),("S21","Yongchun","Blue",4400),("S22","City Hall","Blue",9200),("S23","Sun Yat-Sen Memorial Hall","Blue",6800),("S24","Zhongxiao Dunhua","Blue",7400),("S25","Nanjing Fuxing","Brown",6900),("S26","Technology Building","Brown",4600),("S27","Linguang","Brown",3100),("S28","Xiaobitan","Green",2300),("S29","Tamsui","Red",7000),("S30","Taipei Arena","Green",5300)]
def generate():
 D.mkdir(parents=True,exist_ok=True); pd.DataFrame(STATIONS,columns=['station_id','station','line','hourly_capacity']).to_csv(D/'stations.csv',index=False)
 rng=np.random.default_rng(42); rows=[]
 for dt in pd.date_range('2023-01-01','2023-03-31 23:00',freq='h'):
  for sid,name,line,cap in STATIONS:
   h=dt.hour; peak=np.exp(-((h-8)/2)**2)+np.exp(-((h-18)/2.5)**2); weekend=.7 if dt.weekday()>4 else 1
   ent=max(0,int(cap*(.012+.045*peak)*weekend*rng.normal(1,.12))); ext=max(0,int(ent*rng.normal(.95 if h<12 else 1.05,.12)))
   rows.append((dt.strftime('%Y-%m-%d'),h,sid,name,ent,ext,dt.weekday(),dt.month))
 pd.DataFrame(rows,columns=['date','hour','station_id','station','entries','exits','weekday','month']).to_csv(D/'ridership_hourly.csv',index=False)
 trips=[]
 for i in range(1,2201):
  sid,name,line,cap=STATIONS[i%len(STATIONS)]; day=pd.Timestamp('2023-01-01')+pd.Timedelta(days=i%90); h=6+i%17; minute=(i%6)*10; sched=day+pd.Timedelta(hours=h,minutes=minute)
  delay=max(0,int(rng.gamma(1.5,1.5)+(3 if h in [7,8,9,17,18,19] and rng.random()<.3 else 0)))
  trips.append((f'T{i:05d}',line,sid,name,sched.isoformat(),(sched+pd.Timedelta(minutes=delay)).isoformat(),delay,'synthetic'))
 pd.DataFrame(trips,columns=['train_id','line','station_id','station','scheduled_time','actual_time','delay_minutes','source']).to_csv(D/'train_trips.csv',index=False)
if __name__=='__main__': generate()

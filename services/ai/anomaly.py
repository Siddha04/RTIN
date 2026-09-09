from typing import Any,Dict
import numpy as np
from sklearn.ensemble import IsolationForest
MODEL=IsolationForest(contamination=.25,random_state=42,n_estimators=150)
MODEL.fit(np.array([[40,420,5,.03],[41,430,5,.04],[39,410,6,.02],[42,400,5,.05],[40,415,4,.03],[55,290,7,.10],[37,610,3,.08]]))
def analyze_institution(d:Dict[str,Any])->Dict[str,Any]:
 x=np.array([[d.get('attendance',0),d.get('beneficiaries',0),d.get('inspections',0),d.get('report_variance',0)]],float)
 pred=int(MODEL.predict(x)[0]); decision=float(MODEL.decision_function(x)[0]); anomaly=max(0,min(1,(.15-decision)/.45)); att=float(d.get('attendance',0)); var=float(d.get('report_variance',0)); score=int(round(max(0,min(100,25*anomaly+45*min(abs(att-41)/51,1)+30*min(var/.30,1)))))
 if pred==-1: score=max(score,61)
 band='LOW' if score<=30 else 'MEDIUM' if score<=60 else 'HIGH'
 return {'anomaly':pred==-1,'anomaly_score':round(anomaly,3),'risk_score':score,'risk_band':band,'recommendation':'Priority / surprise inspection' if score>60 else 'More frequent inspection' if score>30 else 'Normal monitoring','reason':'Unusual attendance / record pattern detected' if score>60 else 'Moderate deviation from historical baseline' if score>30 else 'Normal institutional pattern'}

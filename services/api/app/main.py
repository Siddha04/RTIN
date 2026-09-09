from datetime import datetime,timezone
from hashlib import sha256
from fastapi import FastAPI,HTTPException,UploadFile,File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.ai.anomaly import analyze_institution
app=FastAPI(title='INSPECT-AI API',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
USERS={'admin@inspect-ai.local':('Admin@123','ministry'),'inspector@inspect-ai.local':('Inspector@123','inspector'),'ngo@inspect-ai.local':('Ngo@123','ngo')}
DATA=[{'id':'INS-001','name':'Government Higher Secondary School - Salem','district':'Salem','lat':11.6643,'lng':78.1460,'attendance':41,'beneficiaries':412,'inspections':5,'report_variance':.04},{'id':'INS-002','name':'Community Welfare Institute - Erode','district':'Erode','lat':11.3410,'lng':77.7172,'attendance':92,'beneficiaries':510,'inspections':2,'report_variance':.27},{'id':'INS-003','name':'Rural Skills Centre - Namakkal','district':'Namakkal','lat':11.2194,'lng':78.1670,'attendance':55,'beneficiaries':288,'inspections':7,'report_variance':.11},{'id':'INS-004','name':'District Learning Hub - Coimbatore','district':'Coimbatore','lat':11.0168,'lng':76.9558,'attendance':37,'beneficiaries':620,'inspections':3,'report_variance':.08}]
INS=[{'id':'INSP-1001','institution_id':'INS-002','status':'priority','scheduled_at':'2026-09-10T10:30:00Z','inspector':'A. Kumar'},{'id':'INSP-1002','institution_id':'INS-003','status':'assigned','scheduled_at':'2026-09-11T09:00:00Z','inspector':'S. Priya'},{'id':'INSP-1003','institution_id':'INS-001','status':'completed','scheduled_at':'2026-09-09T14:00:00Z','inspector':'M. Ravi'}]
class Login(BaseModel): email:str;password:str
class Inspection(BaseModel): institution_id:str;inspector:str;priority:bool=False
class Evidence(BaseModel): institution_id:str;inspection_id:str;officer_id:str;latitude:float;longitude:float;captured_at:datetime
@app.get('/health')
def health():return {'status':'ok','service':'inspect-ai-api','time':datetime.now(timezone.utc).isoformat()}
@app.post('/api/auth/login')
def login(x:Login):
 u=USERS.get(x.email)
 if not u or u[0]!=x.password: raise HTTPException(401,'Invalid credentials')
 return {'access_token':'demo-token','token_type':'bearer','role':u[1],'email':x.email}
@app.get('/api/institutions')
def institutions():return [{**x,**analyze_institution(x)} for x in DATA]
@app.get('/api/institutions/{id}')
def institution(id:str):
 x=next((x for x in DATA if x['id']==id),None)
 if not x: raise HTTPException(404,'Institution not found')
 return {**x,**analyze_institution(x)}
@app.post('/api/ai/analyze')
def ai(x:dict):return analyze_institution(x)
@app.get('/api/inspections')
def inspections():return [{**x,'institution':next((i['name'] for i in DATA if i['id']==x['institution_id']),x['institution_id'])} for x in INS]
@app.post('/api/inspections')
def create(x:Inspection):
 if not any(i['id']==x.institution_id for i in DATA):raise HTTPException(404,'Institution not found')
 r={'id':f'INSP-{1001+len(INS)}','institution_id':x.institution_id,'status':'priority' if x.priority else 'assigned','scheduled_at':datetime.now(timezone.utc).isoformat(),'inspector':x.inspector};INS.insert(0,r);return r
@app.post('/api/evidence/upload')
async def upload(file:UploadFile=File(...)):
 b=await file.read();return {'filename':file.filename,'sha256':sha256(b).hexdigest(),'verified':True,'uploaded_at':datetime.now(timezone.utc).isoformat()}
@app.post('/api/evidence/verify')
def verify(x:Evidence):
 delta=abs((datetime.now(timezone.utc)-x.captured_at).total_seconds());gps=x.latitude!=0 and x.longitude!=0
 return {'verified':gps and delta<=86400,'checks':{'gps':gps,'timestamp':delta<=86400,'officer_id':bool(x.officer_id),'institution_id':bool(x.institution_id)}}
@app.get('/api/dashboard/summary')
def summary():
 s=[{**x,**analyze_institution(x)} for x in DATA];return {'institutions':len(s),'high_risk':sum(x['risk_score']>=61 for x in s),'medium_risk':sum(31<=x['risk_score']<=60 for x in s),'low_risk':sum(x['risk_score']<=30 for x in s),'active_inspections':sum(x['status']!='completed' for x in INS),'verified_evidence':0,'alerts':sum(x['risk_score']>=61 for x in s),'average_risk':round(sum(x['risk_score'] for x in s)/len(s),1)}

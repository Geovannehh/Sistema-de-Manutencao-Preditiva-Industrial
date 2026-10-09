import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./assetpulse.db')
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
class Base(DeclarativeBase): pass
class Asset(Base):
    __tablename__ = 'assets'
    id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    area = Column(String(100), nullable=False)
class Reading(Base):
    __tablename__ = 'readings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(String(20), ForeignKey('assets.id'), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    temp = Column(Float, nullable=False)
    vibration = Column(Float, nullable=False)
    rpm = Column(Integer, nullable=False)
    current = Column(Float, nullable=False)
class Telemetry(BaseModel):
    asset_id: str = Field(min_length=2, max_length=20)
    temp: float = Field(ge=-40, le=300)
    vibration: float = Field(ge=0, le=200)
    rpm: int = Field(ge=0, le=20000)
    current: float = Field(ge=0, le=1000)

def condition(t):
    # Heurística demonstrativa; NÃO substitui análise profissional ou limites do fabricante.
    if t.vibration >= 9 or t.temp >= 90 or t.current >= 25: return 23, 'critical'
    if t.vibration >= 7 or t.temp >= 80 or t.current >= 20: return 52, 'warning'
    return max(70, round(100 - max(0, t.vibration - 2)*4 - max(0, t.temp - 55)*.7)), 'normal'

def save_reading(session, t):
    if not session.get(Asset,t.asset_id):
        session.add(Asset(id=t.asset_id,name=f'Equipamento {t.asset_id}',area='Área não informada'))
    r=Reading(asset_id=t.asset_id,temp=t.temp,vibration=t.vibration,rpm=t.rpm,current=t.current)
    session.add(r);session.commit();session.refresh(r)
    health,status=condition(t)
    return {'id':r.id,'asset_id':t.asset_id,'timestamp':r.timestamp,'health':health,'status':status}

app=FastAPI(title='AssetPulse API',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('CORS_ORIGINS','http://localhost:5173').split(','),allow_credentials=False,allow_methods=['GET','POST'],allow_headers=['Content-Type'])
@app.on_event('startup')
def startup():
    Base.metadata.create_all(engine)
    seed=[('M-01','Motor de indução','Linha de produção A',67,4.2,1760,13.4),('B-02','Bomba centrífuga','Sistema hidráulico',82,7.8,1440,19.1),('C-03','Compressor de ar','Utilidades',59,2.1,2910,11.3),('M-04','Motor transportador','Esteira principal',94,10.1,1620,25.8),('V-05','Ventilador industrial','Sistema de exaustão',62,3.1,1180,8.7),('P-06','Bomba de processo','Linha de produção B',70,4.7,1720,14.2)]
    with SessionLocal() as db:
        for ident,name,area,t,v,r,c in seed:
            if not db.get(Asset,ident):
                db.add(Asset(id=ident,name=name,area=area));db.add(Reading(asset_id=ident,temp=t,vibration=v,rpm=r,current=c))
        db.commit()
@app.get('/api/health')
def health():return {'ok':True,'service':'assetpulse-api'}
@app.get('/api/assets')
def assets():
    with SessionLocal() as db:
        output=[]
        for a in db.scalars(select(Asset).order_by(Asset.id)):
            r=db.scalars(select(Reading).where(Reading.asset_id==a.id).order_by(Reading.timestamp.desc(),Reading.id.desc()).limit(1)).first()
            if r:
                h,s=condition(Telemetry(asset_id=a.id,temp=r.temp,vibration=r.vibration,rpm=r.rpm,current=r.current))
                output.append({'id':a.id,'name':a.name,'area':a.area,'temp':r.temp,'vibration':r.vibration,'rpm':r.rpm,'current':r.current,'health':h,'status':s})
        return output
@app.post('/api/telemetry',status_code=201)
def receive(t:Telemetry):
    with SessionLocal() as db:return save_reading(db,t)
@app.get('/api/assets/{asset_id}/history')
def history(asset_id:str,limit:int=100):
    with SessionLocal() as db:
        if not db.get(Asset,asset_id):raise HTTPException(status_code=404,detail='Ativo não encontrado')
        readings=db.scalars(select(Reading).where(Reading.asset_id==asset_id).order_by(Reading.timestamp.desc(),Reading.id.desc()).limit(min(max(1,limit),500))).all()
        return [{'timestamp':r.timestamp,'temp':r.temp,'vibration':r.vibration,'rpm':r.rpm,'current':r.current} for r in reversed(readings)]

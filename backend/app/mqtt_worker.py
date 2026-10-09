import os, json, logging, time
import paho.mqtt.client as mqtt
from pydantic import ValidationError
from app.main import Base, engine, SessionLocal, Telemetry, save_reading
logging.basicConfig(level=logging.INFO)
logger=logging.getLogger('assetpulse.mqtt')
Base.metadata.create_all(engine)
def on_connect(client,userdata,flags,reason_code,properties):
    if reason_code == 0: client.subscribe('assetpulse/+/telemetry',qos=1)
    else:logger.error('MQTT connect failed: %s',reason_code)
def on_message(client,userdata,message):
    try:
        payload=json.loads(message.payload.decode('utf-8'))
        t=Telemetry.model_validate(payload)
        topic_asset=message.topic.split('/')[1]
        if t.asset_id!=topic_asset:raise ValueError('asset_id/topic mismatch')
        with SessionLocal() as db:save_reading(db,t)
    except (ValueError,ValidationError,UnicodeDecodeError) as exc:logger.warning('Invalid telemetry: %s',exc)
    except Exception:logger.exception('Error writing telemetry')
client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='assetpulse-worker')
client.on_connect=on_connect;client.on_message=on_message
while True:
    try:client.connect(os.getenv('MQTT_HOST','localhost'),int(os.getenv('MQTT_PORT','1883')),60);client.loop_forever()
    except OSError:logger.warning('Broker unavailable. Retrying...');time.sleep(5)

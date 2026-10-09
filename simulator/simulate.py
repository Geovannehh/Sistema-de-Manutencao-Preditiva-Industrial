import json, os, random, time
import paho.mqtt.client as mqtt
client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(os.getenv('MQTT_HOST','localhost'),int(os.getenv('MQTT_PORT','1883')))
client.loop_start()
assets={'M-01':(67,4.2,1760,13.4),'B-02':(82,7.8,1440,19.1),'C-03':(59,2.1,2910,11.3),'M-04':(94,10.1,1620,25.8),'V-05':(62,3.1,1180,8.7),'P-06':(70,4.7,1720,14.2)}
try:
    while True:
        for aid,(temp,vib,rpm,amp) in assets.items():
            t={'asset_id':aid,'temp':round(temp+random.uniform(-1,1),1),'vibration':round(max(0,vib+random.uniform(-.2,.2)),1),'rpm':int(rpm+random.randint(-10,10)),'current':round(amp+random.uniform(-.25,.25),1)}
            client.publish(f'assetpulse/{aid}/telemetry',json.dumps(t),qos=1)
        print('Telemetria simulada enviada para 6 ativos',flush=True)
        time.sleep(4)
except KeyboardInterrupt:pass
finally:client.loop_stop();client.disconnect()

from flask import Flask, render_template
import datetime
import RPi.GPIO as GPIO
import requests, json
import time
from seeed_dht import DHT
 
app = Flask(__name__)
 
# GPIO SETUP for Moisture Sensor
moisture_channel = 16
GPIO.setmode(GPIO.BCM)
GPIO.setup(moisture_channel, GPIO.IN)
 
dht_sensor = DHT('11', 5)
GPIO.add_event_detect(moisture_channel, GPIO.BOTH, bouncetime=300)
 
 
def read_sensors():
    humi, temp = dht_sensor.read()
    moisture_value = GPIO.input(moisture_channel)
    return temp, humi, moisture_value
 
 
 
def guardar_datos(datos, nombre_archivo:str="display.txt"):
 
    if len(datos) > 9 :
        datos.pop(0)
 
    with open(nombre_archivo, "w") as archivo:
        for datos in datos:
            archivo.write(str(datos)+'\n')
 
 
 
def leer_datos_csv(nombre_archivo:str="display.txt"):
    datos = []
    try:
        with open(nombre_archivo, 'r') as archivo:
            for linea in archivo:
                # Elimina el carácter de nueva línea y divide los valores por comas
                valores = int(linea)
                datos.append(valores)
 
    except Exception as e:
        print(f"Error: Ocurrió un error al leer el archivo '{nombre_archivo}': {e}")
 
    while len(datos)<9:
        datos.insert(0,0)
 
    return datos
 
 
@app.route("/")
def index():
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
 
    temp, humi, moisture_value = read_sensors()
 
    api_key = "9fdb7b9a325ba6eb9a33e8c8c1cfac4d"
 
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    city_name = "Bilbao"
    complete_url = base_url + "appid=" + api_key + "&q=" + city_name
 
    response = requests.get(complete_url)
 
    x = response.json()
 
    if x["main"]:
        y = x["main"]
        current_sensation = y["feels_like"]
    else:
        current_sensation = 0.0
 
    if x["visibility"]:
        visibility = int(x["visibility"])/100
    else:
        visibility = 0.0
 
    if x["wind"]:
        y = x["wind"]
        wind_speed = y["speed"]
    else:
        wind_speed = 0.0
 
    datos = leer_datos_csv()
    datos.append(temp)
    guardar_datos(datos)
 
 
    templateData = {
        'title': 'Sensor Readings',
        'time': timeString,
        'temperature': temp,
        'humidity': humi,
        'moisture_value': moisture_value,
        'soil_condition': 'Wet' if moisture_value else 'Dry',
        'visibility': visibility,
        'temp_sensation' : current_sensation,
        'wind_speed': wind_speed,
        'datos': datos
    }
    
    nuevos_datos = {timeString:[temp,humi,visibility]}
    try:
        # Intentar abrir el archivo JSON existente en modo lectura
        with open("database.json", 'r') as archivo:
            datos_existentes = json.load(archivo)
    except FileNotFoundError:
        datos_existentes = {}
 
    # Agregar nuevos datos al diccionario existente
    datos_existentes.update(nuevos_datos)
 
    # Escribir el diccionario actualizado en el archivo JSON
    with open("database.json", 'w') as archivo:
        json.dump(datos_existentes, archivo, indent=2)

 
    return render_template('index.html', **templateData)
 
 
if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=80, debug=True)
    except KeyboardInterrupt:
        GPIO.cleanup()

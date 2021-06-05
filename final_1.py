import time

import board

import busio

import numpy as np

import statistics as stats

import adafruit_adxl34x

import threading

import serial

import requests

arduino = serial.Serial('/dev/ttyAMA0', baudrate=9600)

i2c = busio.I2C(board.SCL, board.SDA)

accelerometer = adafruit_adxl34x.ADXL345(i2c)

#print("ingrese el valor de N")

#N=int(input())
N=500
medidas = []

lock = threading.Lock()

loop=True

def primerhilo():

  global medidas, lock

  while loop:

    with lock:

      while len(medidas) < N:

        medidas.append(np.array(accelerometer.acceleration))


def segundohilo():

  global medidas, lock

  while loop:

    # esperando señal

    lock.acquire()

    if medidas:
        
      print("Medidas recibidas")

      medidasArray = np.array(medidas)

      medidas = []

      lock.release()

      x = str(float(np.mean(medidasArray[:, 0])))

      y = str(float(np.mean(medidasArray[:, 1])))

      z = str(float(np.mean(medidasArray[:, 2])))

      result = ', '.join([x, y, z]) + "\r\n"

      arduino.write(result.encode())
      print("Enviando a nube...")
      try:
        enviar=requests.get("https://api.thingspeak.com/update?api_key=F1IGQ5QVU3XR6E2X&field1="+str(x)+"&field2="+str(y)+"&field3="+str(z))
      except Exception as ex:
        print(ex)
    #time.sleep(10)
    
      

    else:

      lock.release()

  

def tercerhilo():

  global N, lock

  while loop:

    # f puede ser de la forma ###PROMEDIO-012-###\n

    time.sleep(0.1)
    data = None
    try:
      data=requests.get("https://api.thingspeak.com/channels/1398913/feeds.json?api_key=HD1M52FS8MSAXSI6&results=1").json()
    except Exception as ex:
      print(ex)
      
    if data is not None:
      w=data["feeds"]
    
      print(w)
      r=[]
      for x in w:
        try:
          r.append([float(x['field1']),float(x['field2']),float(x['field3'])])
        except Exception as ex:
          print(ex)  
        
      print("Recibo datos de la nube")
      print(r)
    
    try:
      f=arduino.read(arduino.in_waiting).decode()
    except Exception as ex:
      print(ex)
      f = ""

    if not f.strip():

      continue

    print("Recibido:", f)

    for word in f.split("\n"):

      word = word.strip()

      if word.startswith("###PROMEDIO-") and word.endswith("-###"):

        with lock:

          N = int(f[len("###PROMEDIO-"):len("###PROMEDIO-") + 3])

hilo1 = threading.Thread(target=primerhilo)

hilo2 = threading.Thread(target=segundohilo)

hilo3 = threading.Thread(target=tercerhilo)

hilo1.start()

hilo2.start()

hilo3.start()

input()

loop=False

hilo1.join()

hilo2.join()

hilo3join()

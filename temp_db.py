import RPi.GPIO as GPIO
import sys
import time
import Adafruit_DHT
import pymysql

sensor = Adafruit_DHT.DHT11
conn = pymysql.connect(host="localhost", user="raspi_user", passwd="1234", db="raspi_db")
pin = 4
try:
    with conn.cursor() as cur:
        sql="insert into collect_data values(%s, %s, %s, %s)"
        while True :
            humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
            if humidity is not None and temperature is not None:
               # print (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                print ('Temp = %0.1f*C   Humidity = %0.1f'%(temperature, humidity))
                print ('')
                cur.execute(sql,
                            ('DHT11', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                             temperature, humidity))
                conn.commit()
            else:
                print ("Failed to get reading.")
            time.sleep(1)
except KeyboardInterrupt:
    exit()
finally:
    conn.close()



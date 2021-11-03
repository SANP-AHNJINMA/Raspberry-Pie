import smbus
import RPi.GPIO as GPIO
import time
import spidev
import board
import adafruit_dht
import atexit
import requests

pin = 21
#sensor = adafruit_dht.DHT11(pin)


userID = 'admin1'
houseID = 1
userData = {'houseID':houseID,'userID':userID}

url = 'http://210.182.153.118/'
houseDataPage = 'housedata.php'
getSettingValuePage = 'getsettingvalue.php'

getres = requests.post(url+getSettingValuePage,data=userData)
string = getres.text.split(',')
print(string)
print('')

bus = smbus.SMBus(1)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings (False)
GPIO.setup(17,GPIO.OUT)
GPIO.setup(27,GPIO.OUT)
GPIO.setup(22,GPIO.OUT)
GPIO.setup(26,GPIO.OUT)

#Moter Drive 연결pin
A1A = 5
A1B = 6

#습도 임계치(%)
HUM_THRESHOLD = 35

#센서를 물에 담갔을 때의 토양습도센서 출력값
HUM_MAX = 340

#모터 드라이브 초기설정
GPIO.setup(A1A, GPIO.OUT)
GPIO.output(A1A, GPIO.LOW)
GPIO.setup(A1B, GPIO.OUT)
GPIO.output(A1B, GPIO.LOW)
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = 500000

def setup(Addr):
    global address
    address = Addr
    
def read(chn):  #channel
    
    try:
        if chn == 0:
            bus.write_byte(address, 0X40)   #조도
        if chn == 1:
            bus.write_byte(address, 0X41)   #온도
        if chn == 2:
            bus.write_byte(address, 0X42)   #가변저항
        if chn == 3:
            bus.write_byte(address, 0X43)   #
            bus.read_byte(address)
            
    except Exception as e:
        print ("Address : %s" % address) #예외처리
        print (e)
        
    return bus.read_byte(address)

def write(val):
    try:
        temp = val
        temp = int(temp) # 정수형 변환 
        bus.write_byte_data(address, 0X40, temp)
    except Exception as e:
        print ("Error : Device address: 0x%2X"%address)
        print (e)
        
def read_spi_adc(adcChannel):
    adcValue=0
    buff=spi.xfer2([1,(8+adcChannel)<<4,0])
    adcValue = ((buff[1]&3)<<8)+buff[2]
    #print (adcValue)
    return adcValue
    
def map(value, min_adc, max_adc, min_hum, max_hum):
    adc_range = max_adc-min_adc
    hum_range = max_hum-min_hum
    scale_factor = float(adc_range)/float(hum_range)
    return min_hum+((value-min_adc)/scale_factor)
    
#if __name__=="__main__":    #메인

count = 0

try:
    adcChannel=0
    setup(0x48)
    while True:
        count = (count + 1) % 12
        print('count =',count)
        sensor = adafruit_dht.DHT11(pin)
        #print ('lux = ', read(0))
       # print ('AIN1 = ', read(1))
       # print ('AIN2 = ', read(2))
       # print ('AIN3 = ', read(3))
        print (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        adcValue=read_spi_adc(adcChannel)
        #가져온 데이터를 %단위로 변환, 습도가 높을수록 낮은값을 반환하므로
        #100에서 빼서 습도가 높을수록 백분율이 높아지도록 계산
        hum=100-int(map(adcValue, HUM_MAX, 1023, 0, 100))
        print ('soil Humidity : ',hum , '%', ' lux = ', read(0))
        tmp = read(0)
        tmp = tmp * (255-125)/255+125
        write(tmp)
        h = sensor.humidity
        t = sensor.temperature
        if read(0)>int (string[2]):
            GPIO.output(17,True)
            GPIO.output(27,True)
            GPIO.output(22,True)
            GPIO.output(26,True)
        elif read(0)<= int (string[2]):
            GPIO.output(17,False)
            GPIO.output(27,False)
            GPIO.output(22,False)
            GPIO.output(26,False)
        
        if hum < HUM_THRESHOLD or hum < int (string[1]) : #임계치보다 수분값이 작으면
            GPIO.output(A1A, GPIO.HIGH) #워터펌프 가동
            GPIO.output(A1B, GPIO.LOW)
        elif hum >= HUM_THRESHOLD or hum >= int (string[1]):
            GPIO.output(A1A, GPIO.LOW)
            GPIO.output(A1B, GPIO.LOW)
        
        if h is not None and t is not None :
            print("Temperature = {0:0.1f}*C Humidity = {1:0.1f}%".format(t, h))

            houseDatas = {'houseID':houseID,'temp':t,'moisture':h,'lux':read(0),'soil_moist':hum}

        else :
            print('Read error')

        sensor.exit()

        
        time.sleep(5)

        getres = requests.post(url+getSettingValuePage,data=userData)
        print(getres)
        string = getres.text.split(',')
        print(string)

        if count == 0:
            response = requests.post(url+houseDataPage,data=houseDatas)
            print(response)
            print(response.text)
        print('')

finally:
    GPIO.cleanup()
    spi.close()

@atexit.register
def forcedoff():
    sensor.exit()

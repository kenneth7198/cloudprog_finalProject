import Adafruit_DHT
import csv
import datetime, time

sensor = Adafruit_DHT.DHT11
pin = 27

humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

# 採用增加模式打開dht11.csv檔案，
with open('dht11.csv', 'a') as dhtfile:
    dhtwriter = csv.writer(dhtfile, dialect='excel')
    try:
        while True:
            if humidity is not None and temperature is not None:
                dhtwriter.writerow([datetime.datetime.now().strftime('%y %m %d %H-%m-%S'),
                                    '{:0.1f}C'.format(temperature),
                                    '{:0.1f}%'.format(humidity)])
                # 純檢查是否有輸出，可不用此段程式碼
                print('溫度：{0:0.1f}C 溼度：{1:0.1f}%'.format(temperature, humidity))
            else:
                print('Failed to get reading. Try again!')
            time.sleep(1)
    except KeyboardInterrupt:
        pass
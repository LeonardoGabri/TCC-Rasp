import RPi.GPIO as GPIO
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import pandas as pd
import psycopg2 as pg
import uuid
import configparser
from decimal import Decimal
from datetime import datetime

#Configuração do BD
connection = pg.connect(
    database = 'railway',
    host= 'containers-us-west-147.railway.app',
    user='postgres',
    password='jwiQVvjFu8nG2Yw3rpt5',
    port='5545'
    )
cursor = connection.cursor()
#Variaveis
#variaveis de cominucação com o ads1115
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
canal0 = AnalogIn(ads, ADS.P0)
canal1 = AnalogIn(ads, ADS.P1)

#variaveis da velocidade do vento
pi = 3.14159265
tempo = 5
delaytime = 2000
raio = 147
trigger = 0

#variaveis para medição da velocidade do vento
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)


#Metodos
#retorna a direção do vento por extenso
def direcao(voltagem):
    if (voltagem <= 0.27):
        direcao = "Noroeste"
    elif (voltagem <= 0.32):
        direcao = "Oeste"
    elif (voltagem <= 0.38):
        direcao = "Sudoeste"
    elif (voltagem <= 0.45):
        direcao = "Sul"
    elif (voltagem <= 0.57):
        direcao = "Sudeste"
    elif (voltagem <= 0.75):
        direcao = "Leste"
    elif (voltagem <= 1.25):
        direcao = "Nordeste"
    else:
        direcao = "Norte"
    return direcao;
#retorna a direção do vento por angulo
def direcaoAngulo(voltagem):
    if (voltagem <= 0.27):
        direcao = 315
    elif (voltagem <= 0.32):
        direcao = 270
    elif (voltagem <= 0.38):
        direcao = 225
    elif (voltagem <= 0.45):
        direcao = 180
    elif (voltagem <= 0.57):
        direcao = 135
    elif (voltagem <= 0.75):
        direcao = 90
    elif (voltagem <= 1.25):
        direcao = 45
    else:
        direcao = 0
    return direcao

#calcula as rotações por minuto
def RPMc(counter):
    return ((counter)*60) / tempo

#Calcula a velocidade em metros por segundo
def windSpeed(counter):
    return ((4 * pi * raio * RPMc(counter)) / 60) / 1000

#Calcula a velocidade em kilometros por hora
def speedWind(counter):
    return (((4 * pi * raio * RPMc(counter)) / 60) / 1000)*3.6

#executa todos os processos do calculo de velocidade do vento medido em 5sec.
def velocidade():
    rotacao = 0
    trigger = 0
    horafim = time.time() + tempo #indica o fim do tempo de medição de rotação
    iniciosensor = GPIO.input(4)
    while time.time() < horafim:
        if GPIO.input(4) == 1 and trigger == 0:
            rotacao = rotacao +1
            trigger = 1
        if GPIO.input(4) == 0:
            trigger = 0
        time.sleep(0.001)
    if rotacao == 1 and iniciosensor == 1:
        rotacao = 0
    return round(windSpeed(rotacao), 10)

#Método de inserção de registro no BD
def incluir_registro_anemometro(velocidade, direcao, angulo):
    data_atual = datetime.now()
    
    uuidRandom = uuid.uuid4()
    query = "INSERT INTO anemometro (id, angulo, velocidade, direcao, data) VALUES(%s, %s, %s, %s, %s)"
    cursor.execute(query, (
        str(uuidRandom),
        angulo,
        Decimal(velocidade),
        str(direcao),
        data_atual
    ))
    connection.commit()
    #connection.close()
    print("executou incluir registro")
   
   
def Voltagem():
    volt = canal1.voltage
    print("Sinal captado %.2f" % volt)
    print(canal1.value)
    volt = (volt * 5)
    return volt
#execução
while True:
    """
    print(Voltagem())
    time.sleep(1)
    
    """
    Velocidade  = velocidade()
    print("Velocidade : %.2f metros por segundo." % Velocidade)
    #print(canal0.value, canal0.voltage)
    print("Direção: %s" % direcao(canal0.voltage))
    print("Angulo: %s°" % direcaoAngulo(canal0.voltage))
    incluir_registro_anemometro(Velocidade, direcao(canal0.voltage), direcaoAngulo(canal0.voltage))
    #print(GPIO.input(4))
    print("--o--")
    


        
        
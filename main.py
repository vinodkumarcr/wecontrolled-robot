
from flask import Flask, render_template, Response, stream_with_context, copy_current_request_context 
from camera import VideoCamera
from flask_socketio import SocketIO
from time import sleep
from threading import Thread, Event
#app = Flask(__name__)
#app.config['SECRET_KEY'] = 'secret!'
#socketio = SocketIO(app)

import RPi.GPIO as io   
import Adafruit_DHT
import time
import MCP3208 
io.setmode(io.BCM)
io.setwarnings(False)
pir=13                      #pir sensor
buzz=19
io.setup(pir,io.IN)
io.setup(buzz,io.OUT)
sen=18
buzz=26
io.setup(buzz,io.OUT)
sensor=Adafruit_DHT.DHT11
TRIG1=3 #GPIO03                 Two Ultrasonic sensors
ECHO1=4 #GPIO04
TRIG2=17 #GPIO17
ECHO2=27 #GIO27
motor1a=24              #Two motors
motor1b=23
motor2a=15
motor2b=14
i=1
ser = serial.Serial(gps_port, baudrate = 9600, timeout = 0.5)
def get_distance1(TRIG1,ECHO1):             #get the data from one ultrasonic value in distace
    io.output(TRIG1,io.HIGH)
    time.sleep(0.00001)
    io.output(TRIG1,io.LOW)
    while io.input(ECHO1)==False:
        start=time.time()
    while io.input(ECHO1)==True:
        end=time.time()
    seg_time=end-start
    distance=seg_time/0.000058
    return distance
def get_distance2(TRIG2,ECHO2):              #get the data from one ultrasonic value in distace
    io.output(TRIG2,io.HIGH)
    time.sleep(0.00001)
    io.output(TRIG2,io.LOW)
    while io.input(ECHO2)==False:
        start=time.time()
    while io.input(ECHO2)==True:
        end=time.time()
    seg_time=end-start
    distance=seg_time/0.000058
    return distance
def GPS():                          #GPS value
    try:
        data = ser.readline()
    except:
	print ("loading") 
	#wait for the serial port to churn out data
 
    if data[0:6] == '$GPGGA': # the long and lat data are always contained in the GPGGA string of the NMEA data
 
        msg = pynmea2.parse(data)
 
	#parse the latitude and print
        latval = msg.latitude
	concatlat = "lat:" + str(latval)
	#print concatlat
	longval = msg.longitude
	concatlong = "long:"+ str(longval)
	#print concatlong
           
	time.sleep(0.5)
	return [latval,longval]
adc=MCP3208()

def calculate():

    humidity,temp=Adafruit_DHT.read_retry(sensor,sen)
	print ("humidity:",humidity,"RH")       #HUmidity reading
	print ("temp:",temp,"C")                #temperature value
	gps_coords=GPS()                        #gps coordinates will get
	value=adc.read(0)
	print('gas value:',value)               #gas sensor value and status
	time.sleep(0.5)
	

	if io.input(pir)==True:                 #pir status
            list=['person is detected',gps_coords,humidity,temp,value]
            time.sleep(0.5)
        else:               
            list=[0,'person is not detected',gps_coords,humidity,temp,value]

        
        #list=[0,1,2,3,4]
        return list



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

socketio = SocketIO(app)

thread = Thread()
thread_stop_event = Event()

class CountThread(Thread):
    def __init__(self):
        self.delay = 2
        super(CountThread, self).__init__()

    def ran(self):
        while True:
            temp=calculate()
            print(temp)
            socketio.emit('newnumber', {'number': temp}, namespace='/test')
            sleep(self.delay)

    def run(self):
        self.ran()

@app.route('/')
def index():
        return render_template('index.html')

@socketio.on('connect', namespace='/test')
def test_connect():
    # need visibility of the global thread object
    global thread
    print('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    if not thread.isAlive():
        print("Starting Thread")
        thread = CountThread()
        thread.start()

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')



def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
        
        return Response(gen(VideoCamera()),mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/move_forward/")
def move_forward():                      #motor forward condition
    GPIO.output(motor1a,GPIO.HIGH)
    GPIO.output(motor1b,GPIO.LOW)
    GPIO.output(motor2a,GPIO.LOW)
    GPIO.output(motor2b,GPIO.HIGH)#Moving forward code
    forward_message = "Moving Forward..."
    return render_template('index.html', message=forward_message);

@app.route("/move_reverse/")
def move_reverse():                      #motor reverse condition
    GPIO.output(motor1a,GPIO.LOW)
    GPIO.output(motor1b,GPIO.HIGH)
    GPIO.output(motor2a,GPIO.HIGH)
    GPIO.output(motor2b,GPIO.LOW)
    forward_message = "Moving reverse..."
    return render_template('index.html', message=forward_message);


@app.route("/stop/")
def stop():                         #motor stop condition
    GPIO.output(motor1a,GPIO.LOW)
    GPIO.output(motor1b,GPIO.LOW)
    GPIO.output(motor2a,GPIO.LOW)
    GPIO.output(motor2b,GPIO.LOW)
    forward_message = "Stoping..."
    return render_template('index.html', message=forward_message);


@app.route("/move_right/")
def move_right():                        #motor right condition
    GPIO.output(motor1a,GPIO.HIGH)
    GPIO.output(motor1b,GPIO.LOW)
    GPIO.output(motor2a,GPIO.HIGH)
    GPIO.output(motor2b,GPIO.LOW)
    forward_message = "Moving right..."
    return render_template('index.html', message=forward_message);



@app.route("/move_left/")
def move_left():                         #motor left condition 
        GPIO.output(motor1a,GPIO.LOW)
        GPIO.output(motor1b,GPIO.HIGH)
        GPIO.output(motor2a,GPIO.LOW)
        GPIO.output(motor2b,GPIO.HIGH)
        forward_message = "Moving left..."
        return render_template('index.html', message=forward_message);



if __name__ == '__main__':
    socketio.run(app)
    app.run(host='0.0.0.0', debug=True)

   

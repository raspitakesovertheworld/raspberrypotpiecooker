import os, time, sys, thread
import httplib, urllib, signal
import RPi.GPIO as GPIO
import lirc

#Documentation: config: stop lirc daemon, recognize your remote control, this gives you the codes. Record the button pushes and this will create a config file, which you copy to /etc/lirc/lircd.conf (or without the d).
#Then create a .lircrc file, which maps the buttons to the functions of the socket, that python can read

os.system("modprobe w1-gpio")
os.system("modprobe w1-therm")

logfile="temparature_log_garage"
#devices="28-00000505ac8f"
#devices="28-021460af49ff" 
devices="28-02146065e5ff"


#set initial variables
set_temp=80
set_time=60
system_on=False
fire=0
thread_status_on = True


#GPIO.cleanup()

#GPIO.setmode(GPIO.BOARD)
GPIO.setmode(GPIO.BCM)
GPIO.setup(25, GPIO.OUT)

def signal_handler(signal, frame):

	print "Interrupted/terminated"
        print "Turning off relay..."
	GPIO.output(25, True) #OFF

	GPIO.cleanup()
	thread_on = False

	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def get_temp():
	tfile = open("/sys/bus/w1/devices/"+devices+"/w1_slave")
	text = tfile.read()
	tfile.close()
	temperature_data = text.split()[-1]
	temperature = float(temperature_data[2:])
	temperature = temperature / 1000
	return temperature

def getCPUtemperature():
	res = os.popen('vcgencmd measure_temp').readline()
	return(res.replace("temp=","").replace("'C\n",""))


def post_thingspeak(temp,fire):
	cpu = getCPUtemperature()


#keep the names field1 and field2 etc... they are hardcoded

	params1 = urllib.urlencode({'field1': temp, 'field2': cpu,'field3': fire,'field4': temp * 1.8 + 32, 'key':'GV9GP8H74L71Y9BW'})     
                                     # temp is the data you will be sending to the thingspeak channel for plotting the graph. You can add more than one channel and plot more graphs
        headers = {"Content-typZZe": "application/x-www-form-urlencoded","Accept": "text/plain"}
	conn = httplib.HTTPConnection("api.thingspeak.com:80")
	try:
		conn.request("POST", "/update", params1, headers)
		response = conn.getresponse()
		print response.status, response.reason
		data = response.read()
		conn.close()
		print temp

			
	except:
		print  "connection failed!"                                                                                                                                      


def remote_input_thread(thread_name,delaybox):
	print "thread start"
	global set_temp
	global set_time
	global system_on
	while thread_status_on == True:
	print "before init"
		sockid = lirc.init("myprogram",".lircrc")
        print "before nextcode"
		code_list = lirc.nextcode()
        print "after nextcode"
       		if code_list != []:
                    print "inside if start"
                	code = code_list[0]
                	print code
                	if code == "KEY_VOLUMEUP":
                     	   	set_temp = set_temp + 10
                	if code == "KEY_VOLUMEDOWN":
                        	set_temp = set_temp - 10
                	if code == "KEY_PLAY":
                        	#toggle system
                        	if system_on == True:
                                	system_on = False
                        	else:
                                	system_on = True
                	if code == "KEY_CHANNELUP":
                        	print "temp up!"
                        	set_time = set_time + 10
                	if code == "KEY_CHANNELDOWN":
				set_time = set_time - 10
			

    print "thread end"                                                                                                                                                                                                                                                                                                                                                 
#main look, runs forever
thread.start_new_thread(remote_input_thread,("gurkithread",5,))
while True == True:
	print "main loop starting"
	time_start = int(time.time())
	time_end = time_start + 30


	#writing to file
	##f=open(logfile,"a")
	##ts=time.strftime("%Y-%m-%d %H:%M")
	

	temp=get_temp()
	if system_on == True and int(time.time()) > time_end:
		if temp < set_temp:  # if lower
			GPIO.output(25, False) #ON
			print "Temp is lower, switching ON"
			fire=1
        	if temp >= set_temp: # if highter
			GPIO.output(25, True) #OFF
			print "Temp is higher, switching OFF"
			fire=0
	else:
		GPIO.output(25, True) #OFF

	#post_thingspeak(temp,fire)
	os.system("clear")
	print "System is on: " + str(system_on)
	print "Food temp: " + str(temp)
	print "Fire is: " + str(fire)
	print "Set Temp is: " + str(set_temp)
	print "Set time is: " + str(set_time)
	#f.write(ts+ ", " + str(temp)+"\n")
	#f.close()
	
	
	time.sleep(2)
	

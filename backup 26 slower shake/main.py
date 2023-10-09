from phew import access_point, connect_to_wifi, is_connected_to_wifi, dns, server, ntp
from phew.template import render_template
import json
import machine
import os, sys
import time
from machine import WDT
import cat_feeder
import uasyncio
from umqtt.robust import MQTTClient
loop = uasyncio.get_event_loop()
AP_NAME = "cat_feeder"
AP_DOMAIN = "catfeeder.com"
AP_TEMPLATE_PATH = "ap_templates"
APP_TEMPLATE_PATH = "app_templates"
WIFI_FILE = "wifi.json"
WIFI_MAX_ATTEMPTS = 6
diag_info ="no errors to report"
persistent_vars_filename = "persistent_vars.json"
persistent_vars_dict = {"ssid_ap": "PicoW3",
                        "ap_password" : "123456789",
                        "ADAFRUIT_IO_URL" : "io.adafruit.com",
                        "ADAFRUIT_USERNAME" : b'',
                        "ADAFRUIT_IO_KEY": b'',
                        "ADAFRUIT_IO_FEEDNAME" : b'Open_cat_feeder_input',
                        "ADAFRUIT_IO_FEEDNAME_publish" : b'Open_cat_feeder_status',
                        }
def save_vars():
    global persistent_vars_dict
    vars_dict=persistent_vars_dict
    global_dict_copy = globals()
    for key in vars_dict:
        vars_dict[key] = global_dict_copy[key]   
    with open(persistent_vars_filename, "w") as outfile:
         json.dump(vars_dict, outfile)
         
def restore_vars():
    with open(persistent_vars_filename,"r") as openfile:
        vars_dict = json.load(openfile)
    globals().update(vars_dict)
def cb(topic, msg):# this only gets executed if there is an mqtt message recieved, it's the callback
    try:
        scoops = int(str(msg)[2:-1]) # this might not be quite right. it should be a bytes object, so if we convert it to a string chop off extras then int taht should work.
    except:
        print("there was no message or it was not a valid integer, message was:",str(msg)[2:-1])
    else:
        if 0 <= scoops <= 100: 
            print("scoops command recieved:", scoops)
            #call the scoops dispensing function with the relevant value here.
            cat_feeder.admin_scoops(scoops, wdt)
            return
        print ("ok looks like the commanded number of scoops is not between 0 and 100")
        return
def mqtt_publish(message):
    global mqtt_feedname_publish
    client.publish(mqtt_feedname_publish,    
                   bytes(str(message), 'utf-8'), 
                   qos=0)   
    

def machine_reset():
    time.sleep(1)
    print("Resetting...")
    machine.reset()
def form_submission(request):
    global food_times
    global diag_info 
    submission = request.form["submission"]
    print("got a form submission: ", submission)
    #start the check to see if the submission is probably valid, you could fool this test but at least it prevents accidental mistakes
    try:
        maybe_food_time_list = json.loads(submission)
        print("converted from json: ", maybe_food_time_list)
    except Exception as e:
        print("error:",e)
        diag_info = "could not convert submission into a valid object from json"
        return render_template(f"{APP_TEMPLATE_PATH}/index.html")
    for i in range(len(maybe_food_time_list)):
        if len(maybe_food_time_list[i])==4:
            print("list number ",i," is the right length")
        else:
            print("one of the lists is not the right length",len(maybe_food_time_list[i]))
            diag_info = "one of the lists is not the right length, discarded, no change made"
            return render_template(f"{APP_TEMPLATE_PATH}/index.html")
        if 0 <= maybe_food_time_list[i][0] < 23:
            print("hour field ok")
        else:
            print("hour field borked")
            diag_info = "hour field borked, discarded, no change made"
            return render_template(f"{APP_TEMPLATE_PATH}/index.html")
        if 0 <= maybe_food_time_list[i][1] < 60:
            print("minute field ok")
        else:
            print("minute field borked")
            diag_info = "minute field borked, discarded, no change made"
            return render_template(f"{APP_TEMPLATE_PATH}/index.html")
        if 0 <= maybe_food_time_list[i][2] < 60:
            print("second field ok")
        else:
            print("second field borked")
            diag_info = "second field borked, discarded, no change made"
            return render_template(f"{APP_TEMPLATE_PATH}/index.html")
        if 0 <= maybe_food_time_list[i][3] < 100:
            print("scoops field ok")
        else:
            print("scoops field borked")
            diag_info = "scoops field borked, has to be >0 and <100, discarded, no change made"
            return render_template(f"{APP_TEMPLATE_PATH}/index.html")
    print ("all tests passed, submitted data probably valid, updating food times")
    food_times = maybe_food_time_list
    with open("food_times.json", "w") as f: #save the food times to file
        json.dump(food_times, f)
        f.close()
    diag_info = "succesfully recieved submission and loaded in the new food times"
    return render_template(f"{APP_TEMPLATE_PATH}/index.html")
def application_mode():
    print("Entering application mode.")
    def app_index(request):
        return render_template(f"{APP_TEMPLATE_PATH}/index.html")

    def app_feed_scoop(request):
        cat_feeder.admin_scoops(1, wdt)
        return "OK"
    
    def app_get_temperature(request):
        # Not particularly reliable but uses built in hardware.
        # Demos how to incorporate senasor data into this application.
        # The front end polls this route and displays the output.
        # Replace code here with something else for a 'real' sensor.
        # Algorithm used here is from:
        # https://www.coderdojotc.org/micropython/advanced-labs/03-internal-temperature/
        global food_times
        global diag_info
        return f"{food_times}, Diag info: {diag_info}, current time on the device: {time.localtime()[3:6]} "
    
    def app_reset(request):
        # Deleting the WIFI configuration file will cause the device to reboot as
        # the access point and request new configuration.
        os.remove(WIFI_FILE)
        # Reboot from new thread after we have responded to the user.
        _thread.start_new_thread(machine_reset, ())
        return render_template(f"{APP_TEMPLATE_PATH}/reset.html", access_point_ssid = AP_NAME)

    def app_catch_all(request):
        return "Not found.", 404

    server.add_route("/", handler = app_index, methods = ["GET"])
    server.add_route("/", handler = form_submission, methods = ["POST"])
    server.add_route("/toggle", handler = app_feed_scoop, methods = ["GET"])
    server.add_route("/temperature", handler = app_get_temperature, methods = ["GET"])
    server.add_route("/reset", handler = app_reset, methods = ["GET"])
    # Add other routes for your application...
    server.set_callback(app_catch_all)
def check_time_feed_if_time():
    global food_times
    global diag_info
    food_times_local = food_times
    diag_local = diag_info
    time_of_day = list(time.localtime()[3:6])
    for i in range(len(food_times_local)):
        if time_of_day == food_times_local[i][0:3]:
            print("food time!")
            diag_local = diag_local + " last feeding successfully begun at: " + str(time_of_day)
            cat_feeder.admin_scoops(food_times[i][3], wdt)
        else:
            time.sleep(0.05)
            #print("not a food time yet :(")
    #export data
    food_times_local = food_times
    diag_info = diag_local   
    return

async def mon_for_food_time():
    while True:
        check_time_feed_if_time()
        led.toggle()
        wdt.feed()
        await uasyncio.sleep(0.2)
async def mqtt_out():
    global diag_info
    while True:
        mqtt_publish(diag_info)
        await uasyncio.sleep(30)
async def mqtt_in():
    while True:
        client.check_msg()
        await uasyncio.sleep(4)    
#  initialization/setup section starts here
print("you have a few seconds before I enable the watchdog, which will reset the device if repl is connected")
cat_feeder.bootup()#just put the servo to the zero position in case it's not there already
time.sleep(2)#let wifi reset after boot
with open("food_times.json") as f: # load up the food times from file
    food_times = json.load(f)
    f.close()
try:
    os.stat(WIFI_FILE)#if the file doesn't exist it raises an exception so it skips to the except section
    with open(WIFI_FILE) as f:
        wifi_current_attempt = 1
        wifi_credentials = json.load(f)#this creates a dictionary from the json file       
        while (wifi_current_attempt < WIFI_MAX_ATTEMPTS):
            ip_address = connect_to_wifi(wifi_credentials["ssid"], wifi_credentials["password"])
            if is_connected_to_wifi():
                print(f"Connected to wifi, IP address {ip_address}")
                break
            else:
                wifi_current_attempt += 1            
        if is_connected_to_wifi():
            application_mode()
        else:
            print("Bad wifi connection! Sometimes this just happens even when the credentials are fine:")
            print(wifi_credentials)
            machine_reset()
except Exception as e:
    # Either no wifi configuration file found, or something else went wrong, 
    print("error:",e)
    e = str(e)
    if e == "2":
        print("it's that wacky wifi error, resetting")
        machine.reset()
    if "ENOENT" in e:
        print ("there appears to be no wifi credentials file, you have to put one one the disk there")
    else:
        print("something went wrong when trying to connect to wifi, just reset and try again, could be password is wrong or could be a glitch")
        machine.reset()
globals().update(persistent_vars_dict)#just load the defaults into the global namespace in case there is no persistent vars file
root_files = os.listdir('/')
if 'persistent_vars.json' not in root_files: # if the file doesn't exist in the root then create it with the defaults.
    save_vars()
restore_vars()#if it does exist, just load them in to memory from the file
#this section just tries to get the time three times because I have that rarely, it fails.  It should be replaced with some kind of try and test approach that loops until success is achieved or a timeout occurs
ntp.fetch()
time.sleep(0.3)
ntp.fetch()
time.sleep(0.3)
ntp.fetch()
time.sleep(0.3)
#connect and configure MQTT communication subsystem
mqtt_feedname = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME), 'utf-8')
mqtt_feedname_publish = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME_publish), 'utf-8')
random_num = int.from_bytes(os.urandom(3), 'little')
mqtt_client_id = bytes('client_'+str(random_num), 'utf-8')
client = MQTTClient(client_id=mqtt_client_id, 
                    server=ADAFRUIT_IO_URL, 
                    user=ADAFRUIT_USERNAME, 
                    password=ADAFRUIT_IO_KEY,
                    ssl=False)
wdt = WDT(timeout=4000)# in rare instances the cb function could try to feed the watchdog which would give an error if we don't instantiate it before
client.set_callback(cb)
try:
    print("about to start mqtt connection")
    client.connect()
    mqtt_connected = 1
    print("mqtt connected ok! Recieve feed name:", ADAFRUIT_IO_FEEDNAME, "Status updates feedname:",ADAFRUIT_IO_FEEDNAME_publish)
except Exception as e:
    mqtt_connected = 0
    print('could not connect to MQTT server, oserror -1 or -2 means the adafruit server is not working right: {}{}'.format(type(e).__name__, e))
if mqtt_connected == 1:
    client.subscribe(mqtt_feedname)
led = machine.Pin("LED", machine.Pin.OUT)
server.sched_run()
loop.create_task(mon_for_food_time())
loop.create_task(mqtt_out())
loop.create_task(mqtt_in())
loop.run_forever()
#there is no loop right now. It never gets to this part because the server is a little bit badly made, it loops forever.
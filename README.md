# Open__auto_cat_feeder_v4
Open Source Automatic Cat feeder Pico W Micropython firmware

Simply copy all the files in the main folder onto the memory of the pico W using Thonny.  Do not copy the actual containing outer folder that probably says "backup26" or whatever onto the pico, i.e. the main.py and cat_feeder.py etc that stuff should be on the root of the pico's file system.

Micropython is quite easy to read so there is not too much need for documentation, however fundamentally there is the web server, the mqtt stuff and then there is the cat feeder.   This uses the uasyncio library to run things because I am sort of stuck with that because of how the web server works.

See the manual for configuration information to add the wifi and mqtt login and passwords and stuff, it is a google doc on the google drive folder.

It is reliable but needs some improvement, in particular the web page should be simplified, the javascript stuff removed etc. you can see I just used the temperature display function to do what I wanted without even changing the name.  The web server thing is kind of complicated and I was never really clear on how it worked exactly.

Desireable changes:
- get it to go into AP mode if there is no wifi config file so you can enter config info.  You have to be able to change it if you mess up, there is always USB I guess.  It tried to use the web configurator this was based on, but when it couldn't connect, but the problem is it would fail to connect for any of a dozen reasons and then boot into AP mode and fail to dispense/become inaccessible.  It has to be done carefully and tested thoroughly.
- anything that makes it easier to understand and or more reliable.  Don't use both cores, the threading module is not ready yet and that was a real headache trying to get that not to crash, even the watchdog didn't work properly with that.
- a better interface to set and modify the feeding times
- get time zone implemented, ideally automatically with NTP?  There is probably a way to do this somehow.

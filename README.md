# Open__auto_cat_feeder_v4
Open Source Automatic Cat feeder Pico W Micropython firmware

Simply copy all the files in the main folder onto the memory of the pico W using Thonny.  Do not copy the actual containing outer folder that probably says "backup26" or whatever onto the pico, i.e. the main.py and cat_feeder.py etc that stuff should be on the root of the pico's file system.

Micropython is quite easy to read so there is not too much need for documentation, however fundamentally there is the web server, the mqtt stuff and then there is the cat feeder.

See the manual for configuration information to add the wifi and mqtt login and passwords and stuff, it is a google doc on the google drive folder.

It is reliable but needs some improvement, in particular the web page should be simplified, the javascript stuff removed etc. you can see I just used the temperature display function to do what I wanted without even changing the name.  The web server thing is kind of complicated and I was never really clear on how it worked exactly.

from time import sleep
from machine import PWM, Pin
servo_pin = PWM(Pin(28))
servo_pin.freq(50)

servo_type="180"#put CONTINUOUS for so called 360 degree servos, which are continuous or "180" for a normal servo
PWM_for_cont_servo = 60_000 # if this is wrong it will turn the wrong way, you can adjust it to change the speed
cont_servo_no_motion_pwm = 0
cont_servo_f_motion_pwm = 5700
cont_servo_rotation_time_div_5 = 19.5/50  # this cannot be longer than the watchdog timeout which last I checked was 4 seconds in seconds, if this is too high or too low the feeder will dispense on average slighly too much or too little
def bootup():
    global servo_type
    global cont_servo_no_motion_pwm
    if servo_type  == "180":
        servo_pin.duty_u16(1400)
    if servo_type  == "CONTINUOUS":
        servo_pin.duty_u16(cont_servo_no_motion_pwm)
    return
def servo_angle_speed(angle,speed, pin=servo_pin):#speed is in degrees per second, angle is in degrees.
    max_angle = 180
    min_angle = 0
    max_angle_duty = 8550
    min_angle_duty = 1400
    duty_per_degree = (max_angle_duty-min_angle_duty)/max_angle
    #print("duty per degree:",duty_per_degree)
    speed_duty = speed*duty_per_degree
    #print("speed_duty:",speed_duty)
    goal_duty = min_angle_duty+(duty_per_degree*angle)
    new_duty = pin.duty_u16()
    if angle > max_angle:
        angle = max_angle
    if angle < min_angle:
        angle = min_angle
    while goal_duty - new_duty > 20:
        new_duty = new_duty + 10
        pin.duty_u16(new_duty)
        sleep(10/speed_duty)
    while goal_duty - new_duty < -20:
        new_duty = new_duty - 10
        pin.duty_u16(new_duty)
        sleep(10/speed_duty)
    #print("angle:", angle, "duty:", pin.duty_u16())
def admin_scoops(num_scoops, wdt):
    global servo_type
    global cont_servo_f_motion_pwm
    global cont_servo_rotation_time
    global cont_servo_no_motion_pwm
    print("trying to serve a scoop")
    for i in range (num_scoops):
        if servo_type == "180":
            servo_angle_speed(0,60)
            wdt.feed()
            servo_angle_speed(180,60)
            wdt.feed()
            servo_angle_speed(0,60)
            wdt.feed()
            for x in range(10):#wiggle it to get the kibble to flow around and fill the scoop
                servo_angle_speed(0,130)
                servo_angle_speed(30,130)
                servo_angle_speed(0,130)
            print("scoops served thus far:",i+1)
            wdt.feed()
        if servo_type == "CONTINUOUS":
            servo_pin.duty_u16(cont_servo_f_motion_pwm)
            for x in range (5):# we have to break it up onto fifths because it takes longer to rotate than the watchdog timeout
                sleep(cont_servo_rotation_time_div_5)
                wdt.feed()
                print("got this far1")
            servo_pin.duty_u16(cont_servo_no_motion_pwm)
            print("scoops served thus far:",i+1)
    if servo_type == "180":
        for x in range(13):#wiggle it to get the kibble to flow around and fill the scoop after serving so servo doesn't make noise at rest or dra much current
            servo_angle_speed(0,130)
            servo_angle_speed(30,130)
            servo_angle_speed(0,130)
    #servo_angle_speed(1,60)
    print("done serving ",num_scoops, " scoops, I think.")
bootup()

######################################################################################
## alarm.py 5.00 Home Alarm System                                                  ##
## ---------------------------------------------------------------------------------##
## Works conjunction with host at www.privateeyepi.com                              ##
## Visit projects.privateeyepi.com for full details                                 ##
##                                                                                  ##
## J. Evans April 2013                                                              ##
##                                                                                  ##
## Revision History                                                                 ## 
## V1.00 - Alarm system                                                             ##
## V2.00 - Alarm system & Temperature                                               ##
## V3.00 - Allows changes to GPIO and Locations without a restart                   ##
## V3.10 - Allows Pin 7 to be used interchangeably as an alarm circuit              ##
##         or a thermometer. Thermometer can only be used on pin 7. To configure    ##
##         the alarm define a location linked to Pin 7 as type "Thermometer"        ##
##       - Fix included for flie not found for /sys/bus/w1/devices/xyz/w1_slave     ##
##         This used to cause a crash.                                              ##
## V4.00 - SSL Support will now encrypt all data between Raspberry Pi and Server    ##
##       - Added additional check for temperature logging                           ##
## V5.00 - Support for external siren                                               ##
######################################################################################

import time
import RPi.GPIO as GPIO
import urllib2
import subprocess
global user
global password
global AlarmActioned
global PrintToScreen 
global smtp_server
global smtp_user
global smtp_pass
global GPIOPollInterval
global TemperaturePollInterval
global Farenheit
global GetTemp
global UseSiren
global SirenIsSounding
global ZoneSiren
global SirenPollInterval

#User and password that has been registered on www.privateeyepi.com website
user="alexanderkraft1979@googlemail.com"     #Enter email address here
password="hirsch2myprivateeyepi" #Enter password here

# If you want to receive email alerts define SMTP email server details
# This is the SMTP server, username and password trequired to send email through your internet service provider
smtp_server=""  # usually something like smtp.yourisp.com
smtp_user=""    # usually the main email address of the account holder
smtp_pass=""    # usually your email address password

# Set this to True if you want to send outputs to the screen
# This is useful for debugging
PrintToScreen=False

# Interval in seconds that the alarm system polls the server for changes to zones and locations
GPIOPollInterval=45
TemperaturePollInterval=300

# Set this to true if you want to connect an external siren. Put siren activation and deactivation code in the Siren function.
UseSiren = False

# Poll interval to check server for siren deactivation
SirenPollInterval=5

SirenIsSounding=False

#Indicator to record temperature in Farenheit
Farenheit=False

def fileexists(filename):
    try:
       with open(filename): pass
    except IOError:
       return False     return True

def GetTemperature():
    #Routine to read the temperature
    subprocess.call(['modprobe', 'w1-gpio'])
    subprocess.call(['modprobe', 'w1-therm'])
    
    # Open the file that we viewed earlier so that python can see what is in it. Replace the serial number as before.
    filename = "/sys/bus/w1/devices/28-0000040be5b6/w1_slave"
    if (fileexists(filename)):
        tfile = open(filename)
    else:
        return 0
    # Read all of the text in the file.
    text = tfile.read()
    # Close the file now that the text has been read.
    tfile.close()
    # Split the text with new lines (\n) and select the second line.
    secondline = text.split("\n")[1]
    # Split the line into words, referring to the spaces, and select the 10th word (counting from 0).
    temperaturedata = secondline.split(" ")[9]
    # The first two characters are "t=", so get rid of those and convert the temperature from a string to a number.
    temperature = float(temperaturedata[2:])
    # Put the decimal point in the right place and display it.
    temperature = temperature / 1000
    temp = float(temperature)
    # Do the Farenheit conversion if required
    if Farenheit:
        temp=temp*1.8+32
    temp = round(temp,2)
    return(temp);

def SendEmailAlert(GPIONumber):
    # Import smtplib to provide email functions
    import smtplib
    global PrintToScreen
   
    # Import the email modules
    from email.mime.text import MIMEText

    # Get the email addresses that you configured on the server
    RecordSet = GetDataFromHost(5,[0])
    if RecordSet==False:
        return
    
    numrows = len(RecordSet)
    
    if smtp_server=="":
        return
            
    for i in range(numrows):
        # Define email addresses to use
        addr_to   = RecordSet[i][0]
        addr_from = smtp_user #Or change to another valid email recognized under your account by your ISP      
        # Construct email
        msg = MIMEText(BuildMessage(GPIONumber))
        msg['To'] = addr_to
        msg['From'] = addr_from
        msg['Subject'] = 'Alarm Notification' #Configure to whatever subject line you want
        
        # Send the message via an SMTP server
        s = smtplib.SMTP(smtp_server)
        s.login(smtp_user,smtp_pass)
        s.sendmail(addr_from, addr_to, msg.as_string())
        s.quit()
        if PrintToScreen: print msg;


def BuildGPIOList():
# Build a list of zones and store in memory
# This is run every X seconds set in the PollInterval defined at the top of the program

    global GPIOList
    global numgpio
    global GPIO
    global AlarmActioned

    AlarmActioned = []    
    numgpio=0
    
    RecordSet = GetDataFromHost(2,[0])
    if RecordSet==False:
        return
    
    numgpio = len(RecordSet)
    
    GPIOList = []
    
    for i in range(numgpio):
        GPIOList.append(RecordSet[i][0])
        
    # Initialize the Raspberry Pi board pin numbers to the armed zones
    GPIO.setmode(GPIO.BOARD)
    for i in range(0,numgpio,1):
        GPIO.setup(GPIOList[i], GPIO.IN)
        circuit = GPIO.input(GPIOList[i])
        AlarmActioned.append(circuit)
            
def Siren(Operation):
    global SirenIsSounding
    global PrintToScreen
    
    if UseSiren == False:
        return
    
    if Operation == True and SirenIsSounding == False:
        SirenIsSounding = True
        if PrintToScreen: print "Siren Activated"
        #ActivateSiren Here
    else:
        SirenIsSounding = False
        if PrintToScreen: print "Siren Deactivated"
        #DeactivateSiren Here

def CheckForSirenDeactivation():
    # Routine to fetch the location and zone descriptions from the server 
    global PrintToScreen
    global ZoneSiren 
    
    RecordSet = GetDataFromHost(16,[ZoneSiren])
    if PrintToScreen: print RecordSet
    ZoneStatus=RecordSet[0][0]
    if ZoneStatus=="FALSE":
        Siren(False)    
        
def PollGPIO():
# Routine to continuously poll the IO ports on the Raspberry Pi
    global ciruit
    global GPIOList
    global numgpio
    global GPIO
    global AlarmActioned
    global ZoneSiren
    
    circuit=False
            
    for z in range(0,numgpio,1):
        circuit = GPIO.input(GPIOList[z])
        if circuit==True:
            if not AlarmActioned[z]: 
                AlarmActioned[z]=True
                if (NotifyHostEvent(GPIOList[z])):
                    SendEmailAlert(GPIOList[z]) #IO Port is linked to a zone that is armed, then send email    
                    ZoneSiren = GPIOList[z];
                    Siren(True);
        else: #resetting the IO after the switch is reset (e.g. door closed)
            AlarmActioned[z]=False
                
def NotifyHostEvent(GPIOnumber):

    # Notify the host that an IO was switched (e.g. door open)
    rt=UpdateHost(13,[GPIOnumber])
    # The host will return True if this IO port is linked to a zone that is armed, then send an email
    return(rt)      

def GetTempConfig():
    RecordSet = GetDataFromHost(15, [0])
    if PrintToScreen: print RecordSet
    if RecordSet==False:
        return False
    else:
        rt = RecordSet[0][0]
        if rt == "TRUE":
            return True
        else:
            return False

def NotifyHostTemperature():
    TempBuffer = []
    TempBuffer.append(GetTemperature())
    if Farenheit:
        TempBuffer.append(1)
    else:
        TempBuffer.append(0)
    rt=UpdateHost(14, TempBuffer)
    return (0)

def BuildMessage(GPIOnumber):
    # Routine to fetch the location and zone descriptions from the server 
    global PrintToScreen 
    
    RecordSet = GetDataFromHost(6,[GPIOnumber])
    if PrintToScreen: print RecordSet
    if RecordSet==False:
        return  
    zonedesc=RecordSet[0][0]
    locationdesc = RecordSet[0][1]
    messagestr="This is an automated email from your house alarm system. Alarm activated for Zone: "+zonedesc+" ("+locationdesc+")"
    return messagestr
           
def isNumber(x):
    # Test whether the contents of a string is a number
    try:
        val = int(x)
    except ValueError:
        return False
    return True

def find_all(a_str, sub):
    start = 0
    cnt=0
    while True:
        start = a_str.find(sub, start)
        if start == -1: 
            return cnt
        start += len(sub)
        cnt=cnt+1
    
def UpdateHost(function,opcode):
# Sends data to the server
    global user
    global password
    global PrintToScreen
    
    script_path = "https://privateeyepi.com/alarmhost.php?u="+user+"&p="+password+"&function="+str(function)

    i=0
    for x in opcode:
        script_path=script_path+"&opcode"+str(i)+"="+str(opcode[i])
        i=i+1
    
    if PrintToScreen: print "Host Update: "+script_path 
    try:
        rt=urllib2.urlopen(script_path)
    except urllib2.HTTPError:
        if PrintToScreen: print "HTTP Error"
        return False
    temp=rt.read()
    if PrintToScreen: print temp
    if temp=="TRUE":
        return(1)
    else:
        return(0)

def GetDataFromHost(function,opcode):
# Request data and receive reply (request/reply) from the server
 
    global user
    global password
    global PrintToScreen
    
    script_path = "https://www.privateeyepi.com/alarmhost.php?u="+user+"&p="+password+"&function="+str(function)
    
    i=0
    for x in opcode:
        script_path=script_path+"&opcode"+str(i)+"="+str(opcode[i])
        i=i+1
        
    if PrintToScreen: print script_path 
    try:
        rt = urllib2.urlopen(script_path)
    except urllib2.HTTPError:
        return False
    temp=rt.read()
    if PrintToScreen: print temp
    
    l = find_all(temp,"/n");
    RecordSet = temp.split(',')
    c=[]
    y=0
    c.append([])
    for x in RecordSet:
        if x=="/n":
            y=y+1
            if y < l:
                c.append([])
        else:
            if isNumber(x):
                c[y].append(int(x))
            else:
                c[y].append(x)
        if x=="/FALSE":
            return False    
    return(c)

def PollRoutine():
    global start_time
    global elapsed_time
    global start_temperature_time
    global elapsed_temperature_time
    global numgpio
    global GPIOPollInterval
    global start_siren_time
    global elapsed_siren_time
                    
    # Poll for changes to GPIO settings
    if (elapsed_time > GPIOPollInterval):
        start_time = time.time()
        BuildGPIOList()
        GetTempConfig()

    # Get the latest temperature
    if (elapsed_temperature_time > TemperaturePollInterval):
        start_temperature_time = time.time()
        if GetTemp:
            NotifyHostTemperature();

    # Check if the siren needs deactivation
    if (elapsed_siren_time > SirenPollInterval):
        start_siren_time = time.time()
        if SirenIsSounding:
            CheckForSirenDeactivation()

#Start Main Program Loop

AlarmActioned = []

BuildGPIOList()

GetTemp = GetTempConfig()

if GetTemp:
    NotifyHostTemperature()
 
#Main Loop
# loop to monitor armed zones and create an alarm, and get temperature
start_time = time.time()
start_temperature_time = time.time()
start_siren_time = time.time()

while True:
    
    PollGPIO()
     
    elapsed_time = time.time() - start_time
    elapsed_temperature_time = time.time() - start_temperature_time
    elapsed_siren_time = time.time() - start_siren_time
    
    PollRoutine()
        
    time.sleep(.2)


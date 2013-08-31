######################################################################################
## webcam.py 1.00 Creates an alarm alert from webcam motion                         ##
## ---------------------------------------------------------------------------------##
## Works conjunction with host at www.privateeyepi.com                              ##
## Visit projects.privateeyepi.com for full details                                 ##
##                                                                                  ##
## J. Evans June 2013                                                               ##
##                                                                                  ##
## Revision History                                                                 ## 
## V1.00 - Initial version created                                                  ##
######################################################################################

import time
import urllib2
import subprocess
global user
global password
global PrintToScreen 

#User and password that has been registered on www.privateeyepi.com website
user="alexanderkraft1979@googlemail.com"     #Enter email address here
password="hirsch2myprivateeyepi" #Enter password here

# Set this to True if you want to send outputs to the screen
# This is useful for debugging
PrintToScreen=True
                
def NotifyHostEvent(WebcamNumber):

    # Notify the host that an IO was switched (e.g. door open)
    rt=UpdateHost(13,[WebcamNumber])
    # The host will return True if this IO port is linked to a zone that is armed, then send an email
    return(rt)      
           
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

#Start Main Program

NotifyHostEvent(99)
 

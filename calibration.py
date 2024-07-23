import scipy as sp
import math as m
import numpy as np
import time as time
import matplotlib.pyplot as plt
from enum import Enum


# using S.I units

class activity_unit(Enum):
    BQ = 1 #Bq
    CI = 2 #Ci

activity_unit = Enum('activity_unit', ['BQ','CI'])



# assuming a Cs-137 source, and a collimator made of thick lead of the same width as the GM tube and the same height as the tube, with the point source at the e# ntrance of the channel


P = 370e-3 # source activity (unit determined by used_activity_unit)
used_activity_unit = activity_unit.BQ
# it's better to use a high activity source in order to drive the count at very high levels for dead-time effects to be come noticeable
# the lower the analog frontend dead-time that results in reliable A/D conversion, the higher the activity of the source is required.


Pg = 0.851 # ratio of decays that give rise to gamma photons
µ1 = 0.000103 # linear attenuation coefficient of air for the gamma energy of 667 kEv - emmited by Ba137m
#µ2 = 0.1 # linear attenuation coefficient of beta shield for the gamma energy of 667 kEv. We assume that the beta shield filters beta particles to a negligible amount. 
Al_filter_thickness = 0.001 # cm  0.001 cm = 10µm standard food grade aluminium foil thickness


max_distance = 0.3
distance = 0.15 # distance from point source to center of detector. (meters)
min_distance = 0.05
# GM tube axis is normal to line from point source to GM tube center.

GM_tube_length = 0.075 # glass envelope length only (meters)
GM_tube_diameter = 0.01 # glass envelope diameter (meters)
GM_tube_alpha = 0.0319 # tube efficiency - not all incoming rays trigger an ionization event.
alpha = GM_tube_alpha

GM_tube_detection_cross_section_area = GM_tube_length*GM_tube_diameter
GMT_dcsa = GM_tube_detection_cross_section_area # variable alias

GM_tube_dead_time = 80e-6 # tube intrinsic (charge drift time) dead time
GMT_det = GM_tube_dead_time

if (used_activity_unit == activity_unit.BQ):
    pass
elif (used_activity_unit == activity_unit.CI):
    P *= 3.7e10

#calculate mean path length of gamma rays reaching the tube.
mean_path = (1/GM_tube_length)*((GM_tube_length/2)*(distance**2 + (GM_tube_length/2)**2)**(1/2)) + (distance**2)*m.arcsinh*((GM_tube_length/2)/distance)
#calculate attenuation from linear attenuation coefficient
gamma_att_air = m.exp(-µ1*mean_path)


Al_density = 2.7 # g/cm3
#Al_mass_att_beta_cs137 = 15.1 #cm2/mg
Al_mass_att_beta_cs137 = 15.1e3 #cm2/g beta+/- attenuation for Cs137 emitter https://doi.org/10.1016/j.anucene.2013.07.023
# not used in subsequent calibration formulas, assuming that beta is filtered to an insignificant amount. standard food grade aluminium foil of 10µm thickness gives an attenuation factor in the order of 1e-18

µ2 = Al_mass_att_beta_cs137*Al_density #cm-1
beta_att_Al = m.exp(-Al_filter_thickness*µ2)
# To check the effectiveness of beta filtering.
# not used in subsequent calibration formulas, assuming that beta is filtered to an insignificant amount. standard food grade aluminium foil of 10µm thickness gives an attenuation factor in the order of 1e-18

Al_mass_att_gamma_Ba137m = 7.484e-2 #cm2/g gamma attenuation for Aluminium at 667 kEv
µ3 = Al_mass_att_gamma_Ba137m*Al_density

gamma_att_Al = m.exp(-Al_filter_thickness*µ3)

#calculate total gamma attenuation from air and Al filter.

gamma_att_total = gamma_att_air*gamma_att_Al




import GMobile as GM


# CALIBRATION step 0

# Estimates the analog front end dead-time by timing the pulse width while the GM Tube is exposed to background radiation

background_measure_pulsewidth_total_pulses = 60 # time to spend in seconds measuring pulse width
background_measure_pulsewidth_max_fails = 20 # time to spend in seconds measuring pulse width
rise_timeout_ms = 20000
fall_timeout_ms = 20


(pulsewidth,stdev) = GM.measurePulseWidth(background_measure_pulsewidth_total_pulses,background_measure_pulsewidth_max_fails,rise_timeout_ms,fall_timeout_ms)


# CALIBRATION step 1

#Measure the background CPM with the collimating assembly, but the source removed and far away.
# call main.py and average CPM over specified background_acquire_time in seconds


background_acquire_time = 600 # time to spend in seconds acquiring background radiation levels after first 60 sec of acquisition.


chars = None
chars = input("Step 1 - acquiring background radiation cpm during " + background_acquire_time + " seconds. Please put the source as far away as possible. press ENTER to start")
while chars is None:
    chars = input("Step 1 - acquiring background radiation cpm during " + background_acquire_time + " seconds. Please put the source as far away as possible. press ENTER to start")
    

GM.SetupGPIOEventDetect() # sets up the GPIO event callback

s = 0
cpm_sum = 0
while (s < background_acquire_time):
    cpm = GM.process_events(False,False) # This call should take exactly one second.
    if (cpm != -1):
        cpm_sum += cpm
        s += 1

cpm_background = cpm_sum/background_acquire_time

def model1_estimated_GM_CPM(true_count,t1,t2): # Muller's serial t1 paralyzable dead time followed by t2 non paralyzable dead time model
    alpha = t1/t2
    x = true_count*t2
    corrected_cpm_1 = true_count/((1-alpha)*x + m.exp(alpha*x))
    return corrected_cpm_1

def model2_estimated_GM_CPM(true_count,t1):
    corrected_cpm_2 = true_count*m.exp(-true_count*t1)
    return corrected_cpm_2

def model3_estimated_GM_CPM(true_count,t2):
    corrected_cpm_3 = true_count/(1+true_count*t2)
    return corrected_cpm_3


def movejig(position):

    #TODO : linear actuator positioning code
    err = 0
    
    return err #  err = 0 : actuation OK

def efficiency_step(distance=0.15,movestep=0.005,efficiency_placing_time=600,efficiency_stab_time=60,last_secs_stab_time=60,min_cpm_efficiency_cal=8*cpm_background,max_cpm_efficiency_cal=16*cpm_background):

    # CALIBRATION step 2

    print("Step 2 : automated GM tube efficiency calculation")
        
    s = 0
    s_stab = 0
    cpm_stab = []
    while (s < efficiency_placing_time):
        #print("Step 2.1 - efficiency computation: you have " + efficiency_placing_time + "seconds to put the source at a distance to obtain a reading between " + min_cpm_efficiency_cal + " and " + max_cpm_efficiency_cal + " cpm. press ENTER when in range")
        #print("the timer will start counting down after the first 60 seconds have elapsed - it will then exit the step if cpm is stabilized in range for a whole " + efficiency_stab_time + " secs, and get the cpm average for the last " + last_secs_stab_time + " secs. Do not move the source during that time")
        cpm = GM.process_events(False,False) # This call should take exactly one second.
        if (cpm != -1): # first 60 seconds have elapsed.
            cpm_sum += cpm
            s += 1
            if(cpm > min_cpm_efficiency_cal and cpm < max_cpm_efficiency_cal): # in range.
                s_stab += 1
                cpm_stab.append(cpm)
            elif(cpm > max_cpm_efficiency_cal): # out of range high. reset stabilized countrate time counter
                distance += movestep
                movejig(distance)
                s_stab = 0
                cpm_stab = []
            elif(cpm < min_cpm_efficiency_cal): # out of range high. reset stabilized countrate time counter
                distance -= movestep
                movejig(distance)
                s_stab = 0
                cpm_stab = []
                
            
            print("cpm:\t" + cpm)
            print("stabilized_time:\t" + s_stab)
            print("distance:\t" + distance)
            
            
            if s_stab >= efficiency_stab_time:
                #distance = input("Please input distance in meters from GM_tube to source at stabilized reading")
                cpm_stab = cpm_stab[-last_secs_stab_time:]
                cpm_stab_avg = sum(cpm_stab)/last_secs_stab_time
                break

    cpm_efficiency_calc = cpm_stab_avg - cpm_background

    #calculate mean path length of gamma rays reaching the tube.
    mean_path = (1/GM_tube_length)*((GM_tube_length/2)*(distance**2 + (GM_tube_length/2)**2)**(1/2)) + (distance**2)*m.arcsinh*((GM_tube_length/2)/distance)
    #calculate attenuation from linear attenuation coefficient
    gamma_att_air = m.exp(-µ1*mean_path)

    #calculate total gamma attenuation from air and Al filter.
    gamma_att_total = gamma_att_air*gamma_att_Al


    flux = P*gamma_att_total/(4*m.pi*(distance + 1/(4*m.pi**0.5))**2) # gamma flux in photons.m^2.s^-1 -  accounting for planar cross section of GM Tube (instead of solid angle) and attenuation from air and beta filter
    theoretical_cpm = 60*flux*GMT_dcsa # assuming GM tube efficiency of 1, All photons give rise to ionization events inside the GM tube

    if(s != efficiency_placing_time):
        efficiency = cpm_efficiency_calc/theoretical_cpm
        print("computed efficiency:\t" + efficiency)
        return((efficiency,distance))
    else:
        print("efficiency calibration failed.")
        return((-1,distance))

# Compute efficiency of detection at a count rate sufficiently high enough above background but not as high as dead time effects become significant.
efficiency_placing_time = 600
efficiency_stab_time = 180
last_secs_stab_time = 60
min_cpm_efficiency_cal = 8*cpm_background
max_cpm_efficiency_cal = 16*cpm_background


chars = None
chars = input("Step 2.0 - efficiency computation: please put the source at " + distance + "cm from the GM tube, normal to the tube, withint the collimator. press ENTER to start")

movejig(distance) # initial position
(efficiency,distance) = efficiency_step(distance) # gets efficiency, -1 if failed, and jig to source distance

while (efficiency == -1):
    print("efficiency calculation step failed. repeating")
    (efficiency,distance) = efficiency_step(distance)


#STEP 3 : record countrate while stepping the source jig towards the GM tube
step3_wait_time = 120
step3_last_seconds_measure = 60
step3_last_seconds_measure = min(120,step3_last_seconds_measure) # ensure the total seconds we sample is lower than step3_wait_time
x_distance = np.arange(max_distance,min_distance,-0.005)

y_cpm_m = np.empty(len(x_distance)) # array of average of count rate for each measurement sampling
y_cpm_m[:] = np.nan

y_std_m = np.empty(len(x_distance)) # array of standard deviation of count rate for each measurement sampling
y_std_m[:] = np.nan

y_cpm_t = np.empty(len(x_distance)) # array of theoretical cpms derated with GM tube efficiency
y_cpm_t[:] = np.nan

y_cpm_tm = np.empty(len(x_distance)) # array of theoretical cpms derated with GM tube efficiency and dead time effects
y_cpm_tm[:] = np.nan


distance_cpm_avg_m = np.stack([x_distance,y_cpm_m],axis=1) # tabular data for cpm (average) as a function of source/GM tube distance
distance_cpm_std_m =  np.stack([x_distance,y_std_m],axis=1) # tabular data for cpm (std dev) as a function of source/GM tube distance

distance_cpm_t = np.stack([x_distance,y_cpm_t],axis=1) # tabular data for cpm (theoretical), derated by GM tube efficiency as a function of distance
distance_cpm_tm = np.stack([x_distance,y_cpm_tm],axis=1) # tabular data for cpm (theoretical), derated by GM tube efficiency and accounting for dead time effects


distance = max_distance # retract actuator to minimum to get longest source to GM tube distance.
if not (movejig(distance)): # no actuation error
    idx = 0
    while(distance > min_distance):
        if(movejig(distance)):
            break # actuation error, break loop
        distance -= 0.05
        cpm_stab = [] 
        #TODO : reset deque() in GMobile after jig move, to get rid of the inertia induced by the sliding window sampling
        while(s < step3_wait_time):
            if(s >= (step3_wait_time - step3_last_seconds_measure)):
                cpm_stab.append(GM.process_events(False,False)) # This call should take exactly one second.
            else:
                time.sleep(1)
        cpm_avg = np.average(cpm_stab)
        cpm_std = np.std(cpm_stab)
        distance_cpm_avg_m[idx][1] = cpm_avg
        distance_cpm_std_m[idx][1] = cpm_std
        
        
        #calculate mean path length of gamma rays reaching the tube.
        mean_path = (1/GM_tube_length)*((GM_tube_length/2)*(distance**2 + (GM_tube_length/2)**2)**(1/2)) + (distance**2)*m.arcsinh*((GM_tube_length/2)/distance)
        #calculate attenuation from linear attenuation coefficient
        gamma_att_air = m.exp(-µ1*mean_path)
        #calculate total gamma attenuation from air and Al filter.
        gamma_att_total = gamma_att_air*gamma_att_Al

        flux = P*gamma_att_total/(4*m.pi*(distance + 1/(4*m.pi**0.5))**2) # gamma flux in photons.m^2.s^-1 -  accounting for planar cross section of GM Tube (instead of solid angle) and attenuation from air and beta filter
        theoretical_cpm_eff = 60*flux*GMT_dcsa*efficiency # theoretical cpm (derated with GM tube efficiency estimated in step 2.0)

        distance_cpm_t[idx][1] = theoretical_cpm_eff
        distance_cpm_tm[idx][1] = model1_estimated_GM_CPM(theoretical_cpm_eff)




def compare_cpm_measured_theoretical(theoretical,measured):

    devsum = 0
    devratiosum = 0

    if (len(theoretical) != len(measured)):
        return (-1,-1)
    
    for idx in range(0,len(theoretical)):

        devratiosum += abs((measured[idx][1] - theoretical[idx][1])/measured[idx][1])
        devsum = (measured[idx][1] - theoretical[idx][1])**2

    mape = devratiosum/len(theoretical)
    return (devsum,mape)


print(compare_cpm_measured_theoretical(distance_cpm_tm,distance_cpm_avg_m))







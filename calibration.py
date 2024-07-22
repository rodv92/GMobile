import scipy as sp
import math as m
import numpy as np
import time as time
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


distance = 0.15 # distance from point source to center of detector. (meters)
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



# CALIBRATION step 1

#Measure the background CPM with the collimating assembly, but the source removed and far away.
# call main.py and average CPM over specified background_acquire_time in seconds

import GMobile as GM
background_acquire_time = 600 # time to spend in seconds acquiring background radiation levels after first 60 sec of acquisition.

chars = None
chars = input("Step 1 - acquiring background radiation cpm during " + background_acquire_time + " seconds. Please put the source as far away as possible. press ENTER to start")
while chars is None:
    chars = input("Step 1 - acquiring background radiation cpm during " + background_acquire_time + " seconds. Please put the source as far away as possible. press ENTER to start")
    

s = 0
cpm_sum = 0
while (s < background_acquire_time):
    cpm = GM.process_events(False,False) # This call should take exactly one second.
    if (cpm != -1):
        cpm_sum += cpm
        s += 1

cpm_background = cpm_sum/background_acquire_time

def movejig(position):

    pass


def efficiency_step(distance=0.15,movestep=0.005,efficiency_placing_time=600,efficiency_stab_time=60,last_secs_stab_time=60,min_cpm_efficiency_cal=8*cpm_background,max_cpm_efficiency_cal=16*cpm_background):

    # CALIBRATION step 2

    #chars = None
    #chars = input("Step 2.0 - efficiency computation: please put the source at " + distance + "cm from the GM tube, normal to the tube, withint the collimator. press ENTER to start")
    #while chars is None:
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



movejig(distance) # initial position
efficiency = efficiency_step()
while (efficiency == -1):
    print("efficiency calculation step failed. repeating")
    efficiency = efficiency_step()



#lmbda = (theoretical_cpm_eff/alpha)*GMT_det/60
#alpha*lmbda/GM_det = theo_cpm_eff/60


corrected_cpm = (60/GMT_det)*(1-m.exp(-lmbda - lmbda*(alpha-1)))

print("theoretical cpm not accounting for efficiency:")
print(theoretical_cpm)

print("theoretical cpm accounting for efficiency:")
print(theoretical_cpm_eff)
#print(corrected_cpm_1)



def model1_estimated_GM_CPM(true_count):
    corrected_cpm_1 = (1/GMT_det)*(1-m.exp(-true_count - true_count*(alpha-1)))
    return corrected_cpm_1
def model2_estimated_GM_CPM(true_count):
    corrected_cpm_2 = true_count*m.exp(-true_count*GMT_det)
    return corrected_cpm_2
def model3_estimated_GM_CPM(true_count):
    corrected_cpm_3 = true_count/(1+true_count*GMT_det)
    return corrected_cpm_3

print("lambda")
print(lmbda)
print(alpha*lmbda/GMT_det)
#print(theoretical_cpm_eff/60)
print("poisson model")
print(model1_estimated_GM_CPM(lmbda))
print("paralyzable model")
print(model2_estimated_GM_CPM(theoretical_cpm_eff/60))
print("non paralyzable model")
print(model3_estimated_GM_CPM(theoretical_cpm_eff/60))




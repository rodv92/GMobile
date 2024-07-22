# GMobile
Geiger-Muller counter mobile platform with telemetry

## Features

Pulse counting with Raspberry Pi gpio, with precise timestamping and GPS tagging of each event, LoRa telemetry.

- Using callback function on rising edge of pulse to register count
- TODO : detect falling edge to improve fault detection / out of scale high detection, when the counter is stuck on high
- TODO : Abnormal low count rate detection support (through parametrizable background radiation low count rate threshold) - may indicate counter failure
- TODO : GPIO driven analog frontend test mode - to ensure the analog frontend is operational.
- One thread for "interrupt" handling, other thread for pulse registration and timestamping
- TODO : schedule "interrupt" thread at high priority, make sure threads run on different cores.
- database logging.
- GPS coordinate of event support
- TODO : True count estimation model (Muller's 1973 paper) using serial paralyzable dead-time of tube followed by non-paralyzable dead-time from analog frontend pulse-stretcher.
- isochronous CPM sampling
- TODO : test Lora telemetry mode.
- TODO : test GPS Glonass/Galileo module & implement code support
- TODO : sound card A/D acquisition as an alternative to GPIO.

- calibration.py helper - work in progress

calibration.py is a GM tube calculator helper of the theoretical gamma flux reaching the GM tube from a point source.

These parameters should be supplied :

- Distance from the point source
- Activity at date of manufacture of the source
- Percent accuracy of the activity of the source - for error bar calculation.
- GM tube diameter and length
- background radiation CPM count

- For now, it implies a Cs137 source

Calibration should be done in a lead channel to minimize gamma reflection and destructive interference, and a beta shield is preferable as attenuation coefficient of beta and gamma rays through air does not display the same dynamics.

This theoretical account will allow the determination of the GM tube efficiency
(in the low count regime where dead time has little influence) and will allow comparison between theoretical count and compensated count based on several models. (paralyzable, non paralyzable, or combination of these models in series)

Thus, it will allow to fit the models (mainly by tuning the unknown GM intrinsic dead time) or by using a tailored fitting function for a given tube.

Calibration procedure will require to vary the distance between the source and the tube by known step decrements, and record measured count for each distance knowing the theoretical count.

A linear actuator would allow full automation of the process. 

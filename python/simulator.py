#!/usr/bin/env python3

from datetime import datetime
import time

class Simulator:
    def update(self, val, dt, mx, initval): 
        val = val + dt
        if val > mx: 
            val = initval 
        return val  

    def getTimestamp(self):
        d = datetime.now()
        return int(d.microsecond/1000 + time.mktime(d.timetuple())*1000)

    def getLattitude(self):
        self._lat = self.update(self._lat, 0.00005, 53, 52.168014)
        return  self._lat
    def getLongtitude(self):
        self._lon = self.update(self._lon, 0.00005, 5, 4.412414) 
        return self._lon
    def getAgl(self):
        self._agl = self.update(self._agl, 1.0, 100.0, 0.0) 
        return self._agl
    def getMsl(self): 
        self._msl = self.update(self._msl, 1.0, 100.0, 0.0) 
        return self._msl
    def getHorizAccuracy(self):
        self._horizAccuracy = self.update(self._horizAccuracy, 1.0, 10.0, 0.0) 
        return self._horizAccuracy
    def getYaw(self):
        self._yaw = self.update(self._yaw, 1.0, 360.0, 0.0) 
        return self._yaw
    def getPitch(self): 
        self._pitch = self.update(self._pitch, 1.0, 90.0, -90.0) 
        return self._pitch
    def getRoll(self): 
        self._roll = self.update(self._roll, 1.0, 90.0, -90.0) 
        return self._roll
    def getVelocityX(self): 
        self._velocity_x = self.update(self._velocity_x, 1.0, 100.0, 10.0) 
        return self._velocity_x
    def getVelocityY(self): 
        self._velocity_y = self.update(self._velocity_y, 1.0, 100.0, 10.0) 
        return self._velocity_y 
    def getVelocityZ(self): 
        self._velocity_z = self.update(self._velocity_z, 1.0, 100.0, 10.0) 
        return self._velocity_z
    def getPressure(self): 
        self._pressure = self.update(self._pressure, 0.1, 1013.0, 1012.0) 
        return self._pressure

    _lat = 52.168014
    _lon =  4.412414
    _agl = 0.0
    _msl = 0.0
    _horizAccuracy = 0.0
    _yaw = 0.0
    _pitch = -90.0
    _roll = -90.0
    _velocity_x = 10.0
    _velocity_y = 10.0
    _velocity_z = 10.0
    _pressure = 1012.0
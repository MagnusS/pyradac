'''
Created on 17. des. 2013

@author: tul
'''
import pickle


class RaInfo(object):
    ID=1
    channel=1
    power=1
    beingDisturbed=False


    def __init__(self):
        self.ID=1
        self.channel=1
        self.power=1

    def get_id(self):
        return self.ID


    def get_channel(self):
        return self.channel


    def get_power(self):
        return self.power


    def get_being_disturbed(self):
        return self.beingDisturbed


    def set_id(self, value):
        self.ID = value


    def set_channel(self, value):
        self.channel = value


    def set_power(self, value):
        self.power = value


    def set_being_disturbed(self, value):
        self.beingDisturbed = value

    def pickledObject(self):
        return pickle.dumps(self)

    
 

    
        
        
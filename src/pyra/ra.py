'''
Created on 10. sep. 2013

@author: tul
'''

import random
#import sys
#sys.path.append("../pyradac")
#import ipcclient as pyradac 
#import rainfo

debug=False



class RA():
    Kappan=set()  #The set of channels available to this user
    Kappa=set()    #The total set of channels available
    Pn = 0.0        #The power setting for this user
    #cnR = 20.0        #The data rate satisfaction criterion  for this user (MBit/sec)
    #cnB = 10.0        #The bit error rate satisfaction criterion for this user (%)
    useOnlyLocalInformation=True;
    pin={1:1.0/3, 6:1.0/3, 11:1.0/3 }
    successRate=100.0    #The current measured bit (or packet) success rate
    curTransferRate=0.0  #the last measured transfer rate
    satisfactionTransferRate=20 #the rate at which the router is satisfied
    satisfactionSuccessRate=90.0# in % 
    satisfactionPatience=1  #the number of QoS iterations to wait before informing others about being unhappy
    satisfactionMemory=[]
    neighborWarning=False
    beingDisturbed=False
    id=0
    channel=0
 
 
    
    def __init__(self,id_,useOnlyLocal,patience,satTR,satSR):  #customize the initial state of an object
        self.id=id_
        self.Kappa.add(1) #available channels
        self.Kappa.add(6)
        self.Kappa.add(11)
        self.Kappan=self.Kappan | self.Kappa    #locally available channels
        self.Pn=1                                    #own power level
        self.cn=100                                  #satisfaction criterion, whatever it means
        self.useOnlyLocalInformation=useOnlyLocal
        #self.client=pyradac.IPCClient("127.0.0.1",4001)
        #print "My identifier is", self.client.getIdentifier()
        #self.ownRaInfo=rainfo.RaInfo()  #dette er den delen av konfig-info som sendes til andre ra-er
       # self.pickledString=self.ownRaInfo.pickledObject();
       # print self.pickledString
        #mixed strategy probability function
        self.pin={1:1.0/3, 6:1.0/3, 11:1.0/3 }
        self.selectAction()
        self.Trate=36
        self.trate=24
        self.Prate=1
        self.satisfactionTransferRate=100
        self.satisfactionSuccessRate=0.9
        if patience > 0  :
            self.satisfactionPatience=patience
        else :
            self.satisfactionPatience=1

          #configure radio
        if (debug): print "Setter radio kanal til ", self.channel
        #if self.client.isRadioEnabled():
       #     self.client.setRadioChannelAndTx(self.ownRaInfo.channel, None)
       # else:
        #    print "NB: Radio disabled" 
        
            
            
        #initialize 
        self.initSatisfactionMemory()
        
    def initSatisfactionMemory(self):
        del self.satisfactionMemory[:]
        for ind in xrange(self.satisfactionPatience):
            self.satisfactionMemory.append(1)
        if (debug): print "Sum of satisfaction memory ",sum(self.satisfactionMemory)
            
    def putInSatisfactionMemory(self,value):
        self.satisfactionMemory.pop(0)
        self.satisfactionMemory.append(value)
        if (debug): print "Sum of satisfaction memory ", sum(self.satisfactionMemory)
        
    
        


            
            
      

            
        
    def doChAssign(self):
        #The channel assignment is based on B. Ellingsaeter: Frequency Allocation Game in Satisfaction Form   
        if self.useOnlyLocalInformation:
            self.chAssignLocal()
        else:
            self.chAssignUsingNeighborInfo()
        #print self.pin
        
        
    def selectAction(self):
        #select a new channel based on the pin distribution
        if (debug): print "Select action based on pin"
        aRandomValue=random.random()
        chan=1
        cdfValue=self.pin[chan];
        while ((aRandomValue > cdfValue) and (chan < 11)):
            chan=chan+5
            cdfValue=cdfValue+self.pin[chan]
        if (self.channel) != chan :
            self.nullPerformanceMonitors() 
        self.channel=chan
        #channelConfigString=self.ownRaInfo.pickledObject();
        #self.client.setConfig(channelConfigString)
        #this is test code only
        # newRAinfo=pickle.loads(channelConfigString)
        #print "skriver ut unpickled object"
        #print newRAinfo.beingDisturbed
        #configure radio
        if (debug): print "Changes to channel  ", self.channel
        
        #if self.client.isRadioEnabled():
         #   self.client.setRadioChannelAndTx(self.ownRaInfo.channel, None)
        #else:
         #   print "NB: Radio disabled" 

        
        
    
    def nullPerformanceMonitors(self):
        
        self.Prate=-1  #did not find Prate 
    #    self.trate=-1  #did not find trate
    #    self.Trate=-1  #did not find Trate 
        
        
    def updatePin(self):
        #Based on satisfied information, update the pin distribution
        if (debug): print "Updating pin"
        #TBD update method
      
    def satisfied(self):
        #return TRUE if router base station is satisfied, FALSE if it is not satisfied
        #preliminarily return
        if True: #self.client.isRadioEnabled():
            if (((self.curTransferRate>self.satisfactionTransferRate) and (self.successRate > self.satisfactionSuccessRate)) ) :
                isSatisfied=True
            else :
                isSatisfied=False
        return isSatisfied
    
    def logicalToValue(self, logicalValue):
        value=0
        if (logicalValue==True):
            value=1
        else:
            value=0
        return value
    
    def notSatisfiedAndHasToTellNeighbours(self):
        if (debug): print "Determine if patience is lost such that neighnours will need to be informed"
        if (sum(self.satisfactionMemory) == 0) :          
            isNotSatisfied=True
        else:
            isNotSatisfied=False
        return isNotSatisfied   
        
    def chAssignLocal(self):
        if (debug): print "Assigning a new channel to the AP using only local information"
        self.updatePin()
        if (self.satisfied()):
            if (debug): print "AP satisfied, keeping same channel"
        else:
            if (debug): print "Selecting new channel"            
            self.selectAction()
        if (debug): print self.channel
        
        
    def setNeighborWarning(self):
        if (debug): print "I have received neighbor warnings!!!!!!!"
        self.neighborWarning=True  
              
    #def getNeighborWarnings(self):
    #    print "To get neighbor warnings here"

                 
             
    

        
    def existsNeighborWarning(self):
        return self.neighborWarning
    
    def forgetNeighbourWarnings(self):
        self.neighborWarning=False
    
    def tellNeighborsToChangeStrategy(self):
        if (debug): print "Not satisfied for a long time, complaining to neighbours"
        self.beingDisturbed=True
       
        
        
        
    def chAssignUsingNeighborInfo(self):
        if (debug): print "Assigning a new channel to the AP using also neighbor information"
        self.updatePin()
        if (self.notSatisfiedAndHasToTellNeighbours()) :
            self.tellNeighborsToChangeStrategy()
            self.selectAction()
            self.initSatisfactionMemory() #we have sent out request, we apply a new patience period
            #self.ownRaInfo.set_being_disturbed(False) #or wait till some time later 
            self.forgetNeighbourWarnings() #we have changed our strategy, we may forget previous complaints from neighbours
        else :
            self.putInSatisfactionMemory(self.logicalToValue(self.satisfied())) 
            # uncertain whether put should be here or a different place
            if (self.satisfied() and (self.beingDisturbed)) :
                self.beingDisturbed=False
            
            if ((self.satisfied()) and ( not (self.existsNeighborWarning()))):
                if (debug): print "AP satisfied, keeping same channel"
                # or put the self.ownRaInfo.set_being_disturbed(False) here????
            else:
                if (debug): print "Selecting new channel"            
                self.selectAction()
                self.forgetNeighbourWarnings() #we have changed our strategy, we may forget previous complaints from neighbours
                if (debug): print self.channel
                
    def getAssignedChannel(self):
        #Return the number of the channel that has been selected
        return self.channel
    
    def getID(self):
        #Return this RA's ID (wifi node number)
        return self.id
    
    def getNeigborWarningsFromThisAPID(self):
        #Return true if this RA (AP) is being disturbed 

        return self.beingDisturbed
    
    def getAssignedPower(self):
        return self.Pn
        
    
    def inputCurrentLocalDataRate(self, dRate):
        #for input of the current data rate of this AP
        self.curTransferRate=dRate
        
    def inputCurrentLocalBitSuccessRate(self, dRate):
        #for input of the current data rate of this AP
        self.successRate=dRate
        
    def inputNeighborWarning(self):
        #input neighbor warnings from others, to this node /RA
        self.neighborWarning=True
        
    
        
    
        

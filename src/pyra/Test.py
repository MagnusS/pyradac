'''
Created on 27. mars 2014

@author: tul
'''
import ra
nodeRange=range(1,22)
raList=[]
for node in nodeRange:
    print node
    #create all the RA instances
    #First par: ID number
    #Second par: True if only local decisions (alg 1), False if use neighbor info (alg 2)
    #Third: Memory for neighbor warnings
    #Fourth: satTR, the level at which the transfer rate is satisfied
    #Fifth: satSR, the level at which the success rate is satisfied
    raList.append(ra.RA(node,True,5,20.0,0.0))
    
iterationRange=range(1,10)
for i in iterationRange:
    for anRA in raList:
        print "ID: ", anRA.getID()
        print "Channel: ",anRA.getAssignedChannel()
        print "Warnings:",anRA.getNeigborWarningsFromThisAPID()
    
        #input new information
        anRA.inputCurrentLocalDataRate(1.0)  #datarate in MBit/sek of this AP
        anRA.inputCurrentLocalBitSuccessRate(100.0)  #bit success rate of this RA (set to 100 if unused)
        anRA.inputNeighborWarning() #neighbour warnings issued to anRA
        
        anRA.doChAssign()
        newChannel=anRA.getAssignedChannel()
        print "New Channel:",newChannel
    
    
    
    #get new channel and power
    
    
    
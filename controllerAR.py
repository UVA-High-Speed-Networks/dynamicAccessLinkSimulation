import sys, pdb, csv
import simpy
import Queue
import accessLinkAR as A 
import globals as G
import ipSimulator as IP

numCustomers = int(sys.argv[1])
numHighSpeedPorts = int(sys.argv[2])
mean = G.L**G.alpha/(1-(G.L/G.H)**G.alpha)*G.alpha/(G.alpha-1)*(1/G.L**(G.alpha-1)-1/G.H**(G.alpha-1))
# mean = alpha*L/(alpha-1)*(1-(L/H)**(alpha-1))/(1-(L/H)**alpha)
load = float(sys.argv[3])
# arrivalRate = (mean*8/0.1)/load
arrivalRate = 86400/load
print arrivalRate
W = float(sys.argv[4]) # reservation window, in seconds
lossRate = float(sys.argv[5])


output = 'logs/AR-K' + str(numCustomers) + '-N' + str(numHighSpeedPorts) + '-W' + str(int(W)) + '-load' + str(int(load))  + '-lossRate' + str(lossRate)
with open(output, 'wt') as f:
	writer = csv.writer(f)
	writer.writerow( ('customerId', 'datasetSize(TB)', 'startTimeDelay', 'responseTime', 'circuitOrNot') )

print output

def controller(env, pipe):
	portAvailTime = [0.0 for i in range(numHighSpeedPorts)] # the earliest available time for each port
	lastCustomer = [-1 for i in range(numHighSpeedPorts)] # the last customer that uses each port
	totalTransfers = 0
	delayedTransfers = 0
	while delayedTransfers < G.numDelayed and totalTransfers < 10**8:
		msg = yield pipe.get()
		if msg[0] == 'newRequest':
			minStartTime = env.now + G.timeout
			for i in range(numHighSpeedPorts):
				portAvailTime[i] = max(portAvailTime[i], env.now)	
				if lastCustomer[i] == msg[2]:
					startT = portAvailTime[i]
					reconfig = 0
				else:
					startT = portAvailTime[i] + G.reconfigDelay
					reconfig = G.reconfigDelay
				if startT < minStartTime:	
					minStartTime = startT
					port = i
			if minStartTime - env.now < W: # request is accepted
				circuitDur = msg[3]*1000*8/G.Rc
				portAvailTime[port] = minStartTime + circuitDur		
				lastCustomer[port] = msg[2]	
				msg[1].transfer_proc.interrupt(['circuit', minStartTime - env.now])
			else:
				msg[1].transfer_proc.interrupt(['IP', 0])
			continue		
		if msg[0] == 'transferFinish':
			totalTransfers += 1 
			if msg[1] == True:
				delayedTransfers += 1
				print str(delayedTransfers) + ', ' + str(totalTransfers)
			if delayedTransfers >= G.numDelayed:
				with open(output, 'a') as f:
					writer = csv.writer(f)
					writer.writerow( ('totalTransfers', totalTransfers) )
					writer.writerow( ('delayedTransfers', delayedTransfers) )
				
	if delayedTransfers < G.numDelayed:
		with open(output, 'a') as f:
			writer = csv.writer(f)
			writer.writerow( ('totalTransfers', totalTransfers) )
			writer.writerow( ('delayedTransfers', delayedTransfers) )			

	


	
env = simpy.Environment()
pipe = simpy.Store(env)
ipSim = IP.IPSimulator(env, G.Rh, lossRate)
customers = [A.AccessLink(env, pipe, ipSim.ipPath_proc, lossRate, i, arrivalRate, output) for i in range(numCustomers)] 
ctr = env.process(controller(env, pipe))

env.run(until=ctr)







import sys, pdb, csv
import simpy
import Queue
import accessLinkIR as A 
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
num100GIP = float(sys.argv[6])

output = 'logs/IR-K' + str(numCustomers) + '-N' + str(numHighSpeedPorts) + '-W' + str(int(W)) + '-load' + str(int(load))  + '-lossRate' + str(lossRate) + '-num100GIP' + str(int(num100GIP))
with open(output, 'wt') as f:
	writer = csv.writer(f)
	writer.writerow( ('customerId', 'datasetSize(TB)', 'arrivalTime', 'startTimeDelay', 'responseTime', 'circuitOrNot') )

print output

def controller(env, pipe, customers):
	portAvailability = [1 for i in range(numHighSpeedPorts)] # 1: port idle
	lastCustomer = [-1 for i in range(numHighSpeedPorts)] # the last customer that uses each port
	totalTransfers = 0
	delayedTransfers = 0
	while delayedTransfers < G.numDelayed and totalTransfers < 10**7:
		msg = yield pipe.get()
		if msg[0] == 'newRequest': # ['newRequest', transfer, customerId]
			availPort = -1
			reconfig = 0
			for i in range(numHighSpeedPorts):
				if portAvailability[i] == 1:	
					if lastCustomer[i] == msg[2]:
						availPort = i
						reconfig = 0
						break
					else:
						if availPort == -1:
							availPort = i
							lastCustomer[i] = msg[2]
							reconfig = G.reconfigDelay
			customers[msg[2]].customer_proc.interrupt(['reqReply', availPort]) # inform the customer
			# inform the transfer process
			if availPort >= 0: # request is accepted
				portAvailability[availPort] = 0
				msg[1].transfer_proc.interrupt(['circuit', reconfig])
			else: # blocked request
				msg[1].transfer_proc.interrupt(['IP', 0])
			continue		
		if msg[0] == 'finish':
			totalTransfers += msg[2]
			if msg[3] > 0:
# 				pdb.set_trace()
				print str(delayedTransfers) + ', ' + str(totalTransfers)
				delayedTransfers += msg[3]
			else:
				if totalTransfers%10000 == 0:
					print str(delayedTransfers) + ', ' + str(totalTransfers)
			if delayedTransfers >= G.numDelayed:
				with open(output, 'a') as f:
					writer = csv.writer(f)
					writer.writerow( ('totalTransfers', totalTransfers) )
					writer.writerow( ('delayedTransfers', delayedTransfers) )
			if msg[1] != -1:
				portAvailability[msg[1]] = 1
				
	if delayedTransfers < G.numDelayed:
		with open(output, 'a') as f:
			writer = csv.writer(f)
			writer.writerow( ('totalTransfers', totalTransfers) )
			writer.writerow( ('delayedTransfers', delayedTransfers) )			
		

	
env = simpy.Environment()
pipe = simpy.Store(env)
ipSim = IP.IPSimulator(env, G.Rh, num100GIP, lossRate)
customers = [A.AccessLink(env, pipe, ipSim.ipPath_proc, lossRate, i, arrivalRate, output) for i in range(numCustomers)] 
ctr = env.process(controller(env, pipe, customers))

env.run(until=ctr)

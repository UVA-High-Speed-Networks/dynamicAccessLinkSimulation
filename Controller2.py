import sys, pdb, csv
import simpy
import Queue
import Customer2 as C 

numCustomers = int(sys.argv[1])
numHighSpeedPorts = int(sys.argv[2])
# SIMLT_TIME = int(sys.argv[4])
# shape, scale = 3., 1600/3.  # pareto distribution
alpha, L = 2.0, 1.0 # file transfer size in TB, L: scale (min), alpha: shape
H = 100.0
mean = alpha*L/(alpha-1)*(1-(L/H)**(alpha-1))/(1-(L/H)**alpha)
load = float(sys.argv[3])
# arrivalRate = (mean*8/0.1)/load
arrivalRate = 86400*load
print arrivalRate
delayThreshold = int(sys.argv[4])
numDelayed = int(sys.argv[5])

output = 'logs/K' + str(numCustomers) + '-N' + str(numHighSpeedPorts) + '-load' + str(load) + '-delayThreshold' + str(delayThreshold)
# output = 'logs/K' + str(numCustomers) + '-N' + str(numHighSpeedPorts) + '-load' + str(load) + '-load' + str(delayThreshold)
with open(output, 'wt') as f:
	writer = csv.writer(f)
	writer.writerow( ('customerId', 'delay') )

print output

def controller(env, pipe, customers):
	portAvailability = [1 for i in range(numHighSpeedPorts)] # 1: port idle
	requestQ = Queue.Queue() 
	totalTransfers = 0
	delayedTransfers = 0
	while delayedTransfers < numDelayed:
		msg = yield pipe.get()
# 		pdb.set_trace()
		if msg[0] == 'newRequest':
# 			print str(env.now) + ': New request from customer ' + str(msg[1])
# 			print portAvailability
			availPort = next((i for i, x in enumerate(portAvailability) if x), -1)
			if availPort >= 0:
# 				print 'Allocating...'
				portAvailability[availPort] = 0
				customers[msg[1]].customer_proc.interrupt(['portAllocated', availPort])
			else:
# 				print 'Waiting...'
				requestQ.put(msg[1])
			continue		
		if msg[0] == 'finish':
			totalTransfers += msg[2]
			if msg[3] > 0:
# 				pdb.set_trace()
				print delayedTransfers
			delayedTransfers += msg[3]
			if delayedTransfers >= numDelayed:
				with open(output, 'a') as f:
					writer = csv.writer(f)
					writer.writerow( ('totalTransfers', totalTransfers) )
					writer.writerow( ('delayedTransfers', delayedTransfers) )
# 			print str(env.now) + ': freed port ' + str(msg[1])
			if not requestQ.empty():
# 				print 'Allocating to customer ' + str(msg[1])
				customers[requestQ.get()].customer_proc.interrupt(['portAllocated', msg[1]])
			else:
# 				print 'No more request...'
				portAvailability[msg[1]] = 1

	
env = simpy.Environment()
pipe = simpy.Store(env)
customers = [C.Customer(env, pipe, i, 200000, alpha, L, H, arrivalRate, output, delayThreshold) for i in range(numCustomers)]
ctr = env.process(controller(env, pipe, customers))

env.run(until=ctr)

import sys, pdb, csv
import simpy
import Queue
import customerShared as C 

numUVA = int(sys.argv[1])
numJMU = int(sys.argv[2])
numHighSpeedPorts = int(sys.argv[3])
alpha, L = float(sys.argv[4]), float(sys.argv[5]) # file transfer size in TB, L: scale (min), alpha: shape
H = 100.0
mean = L**alpha/(1-(L/H)**alpha)*alpha/(alpha-1)*(1/L**(alpha-1)-1/H**(alpha-1))
# mean = alpha*L/(alpha-1)*(1-(L/H)**(alpha-1))/(1-(L/H)**alpha)
load = float(sys.argv[6])
# arrivalRate = (mean*8/0.1)/load
arrivalRate = 86400/load
print arrivalRate
delayThreshold = int(sys.argv[7])
numDelayed = int(sys.argv[8])
reconfigDelay = float(sys.argv[9]) # WDM configuration delay, ms

output = 'logs/shared-UVA' + str(numUVA) + '-JMU' + str(numJMU) + '-N' + str(numHighSpeedPorts) + '-alpha' + str(alpha) + '-L' + str(L) + '-reconfig' + str(reconfigDelay) + 'ms-load' + str(load) + '-delayThreshold' + str(delayThreshold)
with open(output, 'wt') as f:
	writer = csv.writer(f)
	writer.writerow( ('customerId', 'datasetSize(TB)', 'startTimeDelay', 'responseTime') )

print output

def controller(env, pipe, customers):
	portAvailability = [1 for i in range(numHighSpeedPorts)] # 1: port idle
	lastCustomer = [-1 for i in range(numHighSpeedPorts)] # the last customer that uses each port
	requestQ = Queue.Queue() 
	totalTransfers = 0
	delayedTransfers = 0
	while delayedTransfers < numDelayed and totalTransfers < 7*10**7:
		msg = yield pipe.get()
# 		pdb.set_trace()
		if msg[0] == 'newRequest':
# 			print str(env.now) + ': New request from customer ' + str(msg[1])
# 			print portAvailability
			availPort = -1
			reconfig = 0
			for i in range(numHighSpeedPorts):
				if portAvailability[i] == 1:	
					if lastCustomer[i] == msg[1]:
						availPort = i
						reconfig = 0
						break
					else:
						if availPort == -1:
							availPort = i
							lastCustomer[i] = msg[1]
							reconfig = reconfigDelay
			if availPort >= 0:
# 				print 'Allocating...'
				portAvailability[availPort] = 0
				customers[msg[1]].customer_proc.interrupt(['portAllocated', availPort, reconfig])
			else:
# 				print 'Waiting...'
				requestQ.put(msg[1])
			continue		
		if msg[0] == 'finish':
			totalTransfers += msg[2]
			if msg[3] > 0:
# 				pdb.set_trace()
				print str(delayedTransfers) + ', ' + str(totalTransfers)
				delayedTransfers += msg[3]
			if delayedTransfers >= numDelayed:
				with open(output, 'a') as f:
					writer = csv.writer(f)
					writer.writerow( ('totalTransfers', totalTransfers) )
					writer.writerow( ('delayedTransfers', delayedTransfers) )
# 			print str(env.now) + ': freed port ' + str(msg[1])
			if not requestQ.empty():
# 				print 'Allocating to customer ' + str(msg[1])
				customerId = requestQ.get()
				if lastCustomer[msg[1]] != customerId:
					reconfig = reconfigDelay
					lastCustomer[msg[1]] = customerId
				else:
					reconfig = 0
				customers[customerId].customer_proc.interrupt(['portAllocated', msg[1], reconfig])
			else:
# 				print 'No more request...'
				portAvailability[msg[1]] = 1
				
	if delayedTransfers < numDelayed:
		with open(output, 'a') as f:
			writer = csv.writer(f)
			writer.writerow( ('totalTransfers', totalTransfers) )
			writer.writerow( ('delayedTransfers', delayedTransfers) )			
		

	
env = simpy.Environment()
pipe = simpy.Store(env)
customers = [C.Customer(env, pipe, i, 200000, alpha, L, H, 3*arrivalRate, output, delayThreshold) for i in range(numUVA)] + [C.Customer(env, pipe, i, 200000, alpha, L, H, arrivalRate, output, delayThreshold) for i in range(numUVA, numUVA+numJMU)]
ctr = env.process(controller(env, pipe, customers))

env.run(until=ctr)

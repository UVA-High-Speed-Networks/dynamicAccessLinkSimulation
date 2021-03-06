from numpy.random import exponential, uniform
import simpy, pdb
import Queue, csv
from math import ceil, sqrt
import globals as G
import ipSimulator as IP


class AccessLink:
	
	def __init__(self, env, pipeToController, ip100GProc, lossRate, id, arrivalRate, output):
		self.id = id
		self.output = output
		self.arrivalRate = arrivalRate
		self.countTotal = 0
		self.countDelay = 0
		self.ip10G = IP.IPSimulator(env, G.Rl, 1, lossRate)
		self.customer_proc = env.process(self.customer(env, pipeToController, ip100GProc, self.ip10G.ipPath_proc))
		
	def customer(self, env, pipeToController, ip100GProc, ip10GProc):
		while True:
			yield env.timeout(exponential(self.arrivalRate))
			U = uniform()
			assert U > 0 and U < 1
			size = ((-U*(G.H**G.alpha) + U*(G.L**G.alpha) + G.H**G.alpha)/(G.H**G.alpha*(G.L**G.alpha)))**(-1/G.alpha)
# 			size = float("{0:.3f}".format(size)) # TB
# 			print size
# 			assert size >= self.L
			newTransfer = Transfer(env, self.id, size, self.output, pipeToController, ip100GProc, ip10GProc)
			pipeToController.put(['newRequest', newTransfer, self.id, size])
	
	
	
class Transfer:
	
	def __init__(self, env, id, size, output, pipeToController, ip100GProc, ip10GProc):
		self.id = id
		self.size = size # TB
		self.sizeLeft = size*8*10**3 # Gbits
		self.blockSize = sqrt(G.Rc*1e9*self.size*1e12*8*G.tau)/1e9/8.0 # in GB
# 		print 'block size: ' + str(self.blockSize) + ', delay: ' + str(self.blockSize*8/G.Rc) + ', ' + str(ceil(self.size*1000/self.blockSize)*G.tau)
		self.requestTime = float("{0:.3f}".format(env.now))
		self.flowRate = 0
		self.estTime2Finish = G.timeout
		self.startTime = -1
		self.output = output
		self.ipSim = None
		self.portId = -1 # only if the transfer is carried on a circuit the value of portId becomes >= 0
		self.flag = False # for start time delay larger than a threshold 
		self.oldTime = -1
		self.transfer_proc = env.process(self.transfer(env, pipeToController, ip100GProc, ip10GProc))
		
	def transfer(self, env, pipeToController, ip100GProc, ip10GProc):
		# wait for the SDN controller to decide whether the transfer should start on a circuit or not
		try: 
			yield env.timeout(G.timeout)
		except simpy.Interrupt as i:
			self.startTime = float("{0:.3f}".format(env.now)) + i.cause[1] 
			if self.startTime - self.requestTime > G.delayThreshold:
# 				print self.startTime - self.requestTime
				self.flag = True
			path = i.cause[0] 
			if path == 'circuit': # the transfer will be carried on a circuit
				self.ipSim = ip100GProc
				env.process(circuit(env, i.cause[1], self.size*1000*8/G.Rc, ip100GProc))
				yield env.timeout(i.cause[1] + self.blockSize*8/G.Rc) # wait for circuit to start and account for store-and-forward delay
			else: # fall back to 10 GE links
				self.ipSim = ip10GProc
# 			print 'before start flow'
# 			pdb.set_trace()
			self.ipSim.interrupt(['flowStart', self])
		
		while self.sizeLeft > 10**-6:
			try: 
				yield env.timeout(self.estTime2Finish)
				self.sizeLeft -= (env.now - self.oldTime)*self.flowRate
			except simpy.Interrupt as i:
# 				pdb.set_trace()
				assert i.cause <= G.Rc
				if self.flowRate > 0:
					self.sizeLeft -= (env.now - self.oldTime)*self.flowRate
				else:
					assert self.oldTime == -1
				self.oldTime = env.now
				self.flowRate = i.cause	
				assert self.flowRate != 0
				self.estTime2Finish = self.sizeLeft/self.flowRate
		
# 		pdb.set_trace()
		self.ipSim.interrupt(['flowFinish', self])
		if path == 'circuit':
			fileOpenOverhead = ceil(self.size*1000/self.blockSize)*G.tau
		else:
			fileOpenOverhead = 0
				
		with open(self.output, 'a') as f:	
			writer = csv.writer(f)
			writer.writerow( (self.id, float("{0:.3f}".format(self.size)), self.requestTime, float("{0:.3f}".format(self.startTime - self.requestTime)), float("{0:.3f}".format(env.now + fileOpenOverhead - self.requestTime)), path) )
		
		pipeToController.put(['transferFinish', self.flag])
		
		finishTime = env.now
		while env.now - finishTime < 0.1:
			try: 
				yield env.timeout(1)
			except simpy.Interrupt as i:
				pass		

	
def circuit(env, waitTime1, waitTime2, ip100GProc):
	yield env.timeout(waitTime1)
# 	print 'before start circuit'
# 	pdb.set_trace()
	ip100GProc.interrupt(['circuitStart'])
	yield env.timeout(waitTime2)
	ip100GProc.interrupt(['circuitEnd'])
	
	
	



	
		
		
		
		
		
		
		
		
		
		
		
		
		
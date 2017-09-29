from numpy.random import exponential, uniform
import simpy, pdb
import Queue, csv
from math import sqrt
import globals as G
import ipSimulator as IP

R = 100.0 # Gbps

class AccessLink:
	
	def __init__(self, env, pipeToController, ip100GProc, lossRate, id, arrivalRate, output):
		self.id = id
		self.output = output
		self.arrivalRate = arrivalRate
		self.portId = -1 # -1 means the customer is not being allocated a circuit
		self.countTotal = 0
		self.countDelay = 0
		self.requests = []
		self.firstReq = None
		self.ip10G = IP.IPSimulator(env, G.Rl, 1, lossRate)
		self.customer_proc = env.process(self.customer(env, pipeToController))
		self.gen_proc = env.process(self.reqGenerator(env, pipeToController, ip100GProc, self.ip10G.ipPath_proc))
		
	def customer(self, env, pipeToController):
		while True:
			try:
				yield env.timeout(G.timeout)
			except simpy.Interrupt as i: 
				if i.cause[0] == 'newTransfer':
					if self.portId < 0: # not being allocated a circuit
						self.firstReq = i.cause[1]
						pipeToController.put(['newRequest', i.cause[1], self.id])
					else: # a second request arrives when the customer is being allocated a circuit
						self.requests.append(i.cause[1])
						i.cause[1].transfer_proc.interrupt(['circuit', 0])
				if i.cause[0] == 'finishTransfer': # ['finishTransfer', transfer, whetherDelayed]
					self.requests.remove(i.cause[1])
					self.countTotal += 1
					if i.cause[2] == True:
						self.countDelay += 1
					if len(self.requests) == 0:
						pipeToController.put(['finish', self.portId, self.countTotal, self.countDelay])
						self.portId = -1
						self.countDelay = 0
						self.countTotal = 0
				if i.cause[0] == 'reqReply':
					self.portId = i.cause[1]
					if i.cause[1] >= 0:
						self.requests.append(self.firstReq)
						self.firstReq = None
	
	def reqGenerator(self, env, pipeToController, ip100GProc, ip10GProc):
		while True:
			yield env.timeout(exponential(self.arrivalRate))
			U = uniform()
			size = ((-U*(G.H**G.alpha) + U*(G.L**G.alpha) + G.H**G.alpha)/(G.H**G.alpha*(G.L**G.alpha)))**(-1/G.alpha)
			newTransfer = Transfer(env, self.id, self.customer_proc, size, self.output, pipeToController, ip100GProc, ip10GProc)
			self.customer_proc.interrupt(['newTransfer', newTransfer])
	

	
class Transfer:
	
	def __init__(self, env, id, customerProc, size, output, pipeToController, ip100GProc, ip10GProc):
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
		self.transfer_proc = env.process(self.transfer(env, customerProc, pipeToController, ip100GProc, ip10GProc))
		
	def transfer(self, env, customerProc, pipeToController, ip100GProc, ip10GProc):
		# wait for the SDN controller to decide whether the transfer should start on a circuit or not
		try: 
			yield env.timeout(G.timeout)
		except simpy.Interrupt as i:
			self.startTime = float("{0:.3f}".format(env.now)) + i.cause[1] 
			assert self.startTime>= self.requestTime
			if self.startTime - self.requestTime > G.delayThreshold:
# 				print self.startTime - self.requestTime
				self.flag = True
			path = i.cause[0] 
			if path == 'circuit': # the transfer will be carried on a circuit
				self.ipSim = ip100GProc
				yield env.timeout(i.cause[1]) # wait for circuit to start 
			else: # fall back to 10 GE links
				self.ipSim = ip10GProc
			self.ipSim.interrupt(['flowStart', self])
		
		while self.sizeLeft > 10**-15:
			try: 
				yield env.timeout(self.estTime2Finish)
				self.sizeLeft -= (env.now - self.oldTime)*self.flowRate
			except simpy.Interrupt as i:
# 				assert i.cause <= (1-G.bgUtil)*G.Rc
				if self.flowRate > 0:
					self.sizeLeft -= (env.now - self.oldTime)*self.flowRate
				else:
					assert self.oldTime == -1
				self.oldTime = env.now
				self.flowRate = i.cause			
				assert self.flowRate != 0
				self.estTime2Finish = self.sizeLeft/self.flowRate
		
		self.ipSim.interrupt(['flowFinish', self])
				
		with open(self.output, 'a') as f:	
			writer = csv.writer(f)
			writer.writerow( (self.id, float("{0:.3f}".format(self.size)), self.requestTime, float("{0:.3f}".format(self.startTime - self.requestTime)), float("{0:.3f}".format(env.now - self.requestTime)), path) )
		
		if path == 'circuit':
			customerProc.interrupt(['finishTransfer', self, self.flag])
		else:
			pipeToController.put(['finish', -1, 1, int(self.flag==True)])
		
		finishTime = env.now
		while env.now - finishTime < 0.1:
			try: 
				yield env.timeout(1)
			except simpy.Interrupt as i:
				pass	



	
		
		
		
		
		
		
		
		
		
		
		
		
		
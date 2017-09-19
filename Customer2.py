from numpy.random import exponential, uniform
import simpy, pdb
import Queue, csv

R = 100.0 # Gbps
D = 120.0 # WDM configuration delay, 2 min

class Customer:
	
	def __init__(self, env, pipeToController, id, timer, alpha, L, H, arrivalRate, output, delayThreshold):
		self.id = id
		self.alloStatus = 0 # whether the customer is allocated a port
		self.timer = timer
		self.alpha = alpha
		self.L = L
		self.H = H
		self.output = output
		self.arrivalRate = arrivalRate
		self.delayThreshold = delayThreshold
		self.portId = -1
		self.countTotal = 0
		self.countDelay = 0
		self.requests = []
		self.customer_proc = env.process(self.customer(env, pipeToController))
		self.gen_proc = env.process(self.reqGenerator(env))
		
	def customer(self, env, pipeToController):
		while True:
			try:
				yield env.timeout(self.timer)
			except simpy.Interrupt as i: 
				if i.cause[0] == 'newTransfer':
# 					print str(env.now) + ': New transfer from customer ' + str(self.id)
					pipeToController.put(['newRequest', self.id])
				if i.cause[0] == 'finishTransfer':
					self.requests.remove(i.cause[3])
					self.countTotal += 1
					if i.cause[2] == True:
						self.countDelay += 1
					if len(self.requests) == 0:
						self.alloStatus = 0
						self.portId = -1
						pipeToController.put(['finish', i.cause[1], self.countTotal, self.countDelay])
						self.countDelay = 0
						self.countTotal = 0
					else:
						self.updateRate(R/len(self.requests))
				if i.cause[0] == 'portAllocated':
					self.alloStatus = 1
					self.portId = i.cause[1]
					yield env.timeout(D) # WDM configuration delay
					self.updateRate(R/len(self.requests))
	
	def reqGenerator(self, env):
		while True:
			yield env.timeout(exponential(self.arrivalRate))
			U = uniform()
			size = ((-U*self.H**self.alpha + U*self.L**self.alpha + self.H**self.alpha)/(self.H**self.alpha*self.L**self.alpha))**(-1/self.alpha)
			size = float("{0:.3f}".format(size)) # TB
# 			print str(env.now) + ', new request from customer ' + str(self.id) + ' of size ' + str(size) + ' TB, total requests: ' + str(len(self.requests)+1)
			if self.alloStatus == 0:
				rate = 0
			else:
				rate = R/(len(self.requests)+1)
				self.updateRate(rate)
			newTransfer = Transfer(env, self.id, self.timer, self.customer_proc, size, self.output, self.delayThreshold, rate, self.portId)
			self.requests.append(newTransfer)
			if len(self.requests) == 1:
				self.customer_proc.interrupt(['newTransfer'])			
	
	def updateRate(self, newRate):
		for t in self.requests:
			t.transfer_proc.interrupt([self.portId, newRate])
	
	
class Transfer:
	
	def __init__(self, env, id, timer, customer, size, output, delayThreshold, rate, portId):
		self.id = id
		self.duration = float("{0:.3f}".format(size*8*10)) # seconds
		self.sizeLeft = size*8*10**3 # Gbits
		self.flowRate = rate
		if self.flowRate != 0:
			self.estTime2Finish = self.sizeLeft/self.flowRate
		else:
			self.estTime2Finish = timer	
		self.customer = customer
		self.output = output
		self.portId = portId 
		self.delayThreshold = delayThreshold
		self.flag = False
		self.startTime = float("{0:.3f}".format(env.now))
		self.oldTime = env.now
		self.transfer_proc = env.process(self.transfer(env))
		
	def transfer(self, env):
		while self.sizeLeft > 10**-15:
			try: 
				yield env.timeout(self.estTime2Finish)
				self.sizeLeft -= (env.now - self.oldTime)*self.flowRate
			except simpy.Interrupt as i:
# 				pdb.set_trace()
				if self.flowRate == 0:
					curTime = float("{0:.3f}".format(env.now))
# 					pdb.set_trace()
					if curTime - self.startTime > self.delayThreshold:
						self.flag = True
					if i.cause[1] == 0:
						pdb.set_trace()
# 					if curTime - self.startTime > 0.001:
						
				self.portId = i.cause[0]
				self.sizeLeft -= (env.now - self.oldTime)*self.flowRate
				self.oldTime = env.now
				self.flowRate = i.cause[1]			
				if self.flowRate != 0:
					self.estTime2Finish = self.sizeLeft/self.flowRate
			
# 		print str(env.now) + ', Transfer is finished for customer ' + str(self.id)
# 		if self.flag == True:
# 			pdb.set_trace()
		with open(self.output, 'a') as f:	
			writer = csv.writer(f)
			writer.writerow( (self.id, self.duration, float("{0:.3f}".format(env.now - self.startTime))) )
		self.customer.interrupt(['finishTransfer', self.portId, self.flag, self])
		finishTime = env.now
		while env.now - finishTime < 0.1:
			try: 
				yield env.timeout(1)
			except simpy.Interrupt as i:
				pass		




	
		
		
		
		
		
		
		
		
		
		
		
		
		
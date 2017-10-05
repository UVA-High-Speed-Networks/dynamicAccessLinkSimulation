import simpy, pdb, csv
from math import sqrt
import globals as G

class IPStorage:
	
	def __init__(self, env, capacity, numWavelengths, lossRate, output):
		self.output = output
		self.maxStorageUtil = 0 # in Gbits
		self.lastEventTime = 0
		self.lastStorage = 0
		self.numCircuits = 0 # number of active circuits
		self.flows = []
		self.effeCapacity = min(capacity*(1-G.bgUtil), 1.22*G.MSS*8/(G.RTT*sqrt(lossRate))/1e9)*numWavelengths # in Gbps
		self.ipPath_proc = env.process(self.ipPath(env))
		
	def ipPath(self, env):	
		while True:
			try: 
				yield env.timeout(G.timeout)
			except simpy.Interrupt as i:
# 				print str(env.now) + ': ' + i.cause[0]
				if i.cause[0] == 'flowStart':
					self.updateStorage(env)
					self.flows.append(i.cause[1])
					self.updateRate()
				if i.cause[0] == 'flowFinish':
					self.updateStorage(env)
					self.flows.remove(i.cause[1])
					if len(self.flows) != 0:
						self.updateRate()
				if i.cause[0] == 'circuitStart':
					self.updateStorage(env)
					self.numCircuits += 1
				if i.cause[0] == 'circuitEnd':
					self.updateStorage(env)
					self.numCircuits -= 1		
				if i.cause[0] == 'simFinish':
					with open(self.output, 'a') as f:
						writer = csv.writer(f)
						writer.writerow( ('maxStorageUtil', self.maxStorageUtil/8) ) # in GB

	def updateRate(self):
		newRate = min(G.Rc, self.effeCapacity/len(self.flows))
		for t in self.flows:
			t.transfer_proc.interrupt(newRate)
			
	def outBoundCapacity(self):
		if len(self.flows) == 0:	
			return 0
		elif len(self.flows) == 1:
			return G.Rc
		else:
			return self.effeCapacity
			
	def updateStorage(self, env):		
		rateDiff = self.numCircuits*G.Rc - self.outBoundCapacity() # in Gbps
		self.lastStorage += (round(env.now, 3)-self.lastEventTime)*rateDiff	
		self.lastStorage = round(max(self.lastStorage, 0),3)
# 		print 'time: ' + str(round(env.now, 3))
# 		print 'numCircuits: ' + str(self.numCircuits)
# 		print 'numFlows: ' + str(len(self.flows))
# 		print 'rateDiff: ' + str(rateDiff)
# 		print 'lastStorage: ' + str(self.lastStorage)
# 		pdb.set_trace()
# 		if self.lastStorage < 0:
# 			print self.lastStorage
# 			pdb.set_trace()
		self.maxStorageUtil = max(self.maxStorageUtil, self.lastStorage)
		self.lastEventTime = round(env.now, 3)
			
			
			
			
			
			
			
			
			
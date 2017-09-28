import simpy, pdb
from math import sqrt
import globals as G

class IPSimulator:
	
	def __init__(self, env, capacity, lossRate):
		self.flows = []
		self.effeCapacity = min(capacity*(1-G.bgUtil), 1.22*G.MSS*8/(G.RTT*sqrt(lossRate))/1e9)
		self.ipPath_proc = env.process(self.ipPath(env))
		
	def ipPath(self, env):	
		while True:
			try: 
				yield env.timeout(G.timeout)
			except simpy.Interrupt as i:
				if i.cause[0] == 'flowStart':
					self.flows.append(i.cause[1])
					self.updateRate()
				else: # 'flowFinish'
					self.flows.remove(i.cause[1])
					if len(self.flows) != 0:
						self.updateRate()

	def updateRate(self):
		newRate = self.effeCapacity/len(self.flows)
		for t in self.flows:
			t.transfer_proc.interrupt(newRate)
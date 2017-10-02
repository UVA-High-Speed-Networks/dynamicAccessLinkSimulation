import sys, csv, pdb

mode = sys.argv[1]
numHighSpeedPorts = 4
W = 8000
load = 5
lossRate = 1e-11
num100GIP = 2

if mode == 'AR':
	result = 'logs/results'+mode+'-W'+str(W)+'-sharedPorts'+str(numHighSpeedPorts)+'-load'+str(load)+'-loss'+str(lossRate)+'-num100GIP'+str(int(num100GIP))+'.csv'
else:
	result = 'logs/results'+mode+'-sharedPorts'+str(numHighSpeedPorts)+'-load'+str(load)+'-loss'+str(lossRate)+'-num100GIP'+str(int(num100GIP))+'.csv'

with open(result, 'wt') as csvfile:
	writer = csv.writer(csvfile)
	writer.writerow( ('mode', 'numCustomers', 'numHighSpeedPorts', 'W', 'load', 'lossRate', 'num100GIP', 'numTransfers', 'numBlocked', 'blockingProb', 'aveResponseTime', 'aveRespsTimeCircuit', 'aveRespsTime10GIP') )
	
for numCustomers in range(15, 16):
	output = 'logs/' + mode + '-K' + str(numCustomers) + '-N' + str(numHighSpeedPorts) + '-W' + str(int(W)) + '-load' + str(int(load))  + '-lossRate' + str(lossRate) + '-num100GIP' + str(int(num100GIP))
	print output
	numTransfers = 0
	numBlocked = 0
	responseTime = 0
	responseTimeBlocked = 0
	with open(output, 'r') as csvfile:
		csvfile.readline()
		csvreader = csv.reader(csvfile, delimiter=",")
		for line in csvreader:
			if len(line) < 6:
				continue
			numTransfers += 1
			responseTime += float(line[4])
			if line[5] == 'IP':
				numBlocked += 1
				responseTimeBlocked += float(line[4])
				
	blockingProb = float(numBlocked)/numTransfers	
	aveResponseTime = responseTime/float(numTransfers)
	aveRespsTimeCircuit = (responseTime-responseTimeBlocked)/float(numTransfers-numBlocked) 
	if numBlocked != 0:
		aveRespsTime10GIP = responseTimeBlocked/float(numBlocked)
	else:
		aveRespsTime10GIP = -1
	
	with open(result, 'a') as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow( (mode, numCustomers, numHighSpeedPorts, W, load, lossRate, num100GIP, numTransfers, numBlocked, blockingProb, aveResponseTime, aveRespsTimeCircuit, aveRespsTime10GIP) )
		

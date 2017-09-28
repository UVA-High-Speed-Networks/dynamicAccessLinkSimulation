Rc = 100.0 # circuit capacity
Rh = 100.0 # 100 Gbps IP
Rl = 10.0 # 10 Gbps IP
bgUtil = 0.4 # percentage of bandwidth used by background traffic
RTT = 0.05 # 50 ms
MSS = 1460 # maximum segment size, Bytes

H = 100.0 # pareto max. value, in TB
L = 0.01
alpha = 1e-10
reconfigDelay = 0.01 # WDM configuration delay, 10 ms

tau = 0.001 # file open-and-close overhead, 1 ms
blockSize = 1.0 # size of file blocks for pipelining, in GB

timeout = 200000
delayThreshold = 300 # in seconds
numDelayed = 10000


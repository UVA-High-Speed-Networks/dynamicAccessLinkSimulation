#!/bin/bash

numPorts=(1 2 3 4)
load=(1 5 10)
W=(1000 8000)
lossRate=(4e-11 1e-11)

for index in `seq 0 3`
do
	p=${numPorts[index]}
	for ((i=$[p+1]; i<=20; i++))
	#for ((i=11; i<=20; i++))
	do
		RES=$(sbatch simulation.slurm $i $p 5 8000 1e-11)
		echo $RES
	done
done

#!/bin/bash

#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH -t 10:00:00
#SBATCH -p largemem
#SBATCH -A hntes_group
#SBATCH --mem=20000

module load python/2.7.6
stdbuf -o0 -e0 time python controllerAR.py $1 $2 $3 $4 $5 $6


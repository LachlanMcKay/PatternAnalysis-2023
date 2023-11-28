#!/bin/bash
# set the number of nodes
#SBATCH --nodes=1

# number of CPU cores per task
#SBATCH --cpus-per-task=4

#SBATCH --partition=vgpu

#SBATCH --gres=gpu:1

#SBATCH --job-name=T_Classifier

#SBATCH --mail-type=ALL
#SBATCH --mail-user=tong.qiu@uqconnect.edu.au

conda activate metadamagenet
python3 train.py -m Classification -bm ./model/Triplet.pth
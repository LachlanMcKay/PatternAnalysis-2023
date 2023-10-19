#!/bin/bash
time=0-00:00:10
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --partition=vgpu
#SBATCH --job-name="siamese"
#SBATCH --account=s4589541
#SBATCH --mail-user=s4589541@student.uq.edu.au
#SBATCH --mail-type=BEGIN
#SBATCH --mail-type=END
#SBATCH --mail-type=FAIL
#SBATCH —output=output_dir/%j.out
conda activate /home/Student/s4589541/miniconda3/envs/venv
python /home/Student/s4589541/comp3710/report/PatternAnalysis-2023/recognition/Siamese\ Classifier\ for\ Alzheimer\'s\ disease\ \(s4589541\)/train.py
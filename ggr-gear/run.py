import flywheel
import os
import sys

#get context through fw
context = flywheel.GearContext()
config = context.config

#declare one required flag parameters as folder with dxm

path1 = context.get_input('niftifileone')['location']['path']
path2 = context.get_input('niftifiletwo')['location']['path']
path3 = context.get_input('niftifilethree')['location']['path']


tempstr = "/flywheel/v0/output/data/"
outputstr = "/flywheel/v0/output/recons/"
workingstr = "/flywheel/v0/output/working/"
os.system("mkdir " + tempstr)
os.system("cp " + str(path1) + " " + str(path2) + " " + str(path3) + " /flywheel/v0/output/data")
os.system("pwd")
os.system("ls output/data")
os.system("cd /flywheel/v0/output && python3 /opt/GGR-recon/preprocess.py")
os.system("cd /flywheel/v0/output && python3 /opt/GGR-recon/recon.py --keep-negative-values --ggr -w 0.03")
os.system("rm -rf " + tempstr)
os.system("rm -rf " +  workingstr)

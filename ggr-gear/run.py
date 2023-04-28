import flywheel
import os
import sys
import logging

#get context through fw
context = flywheel.GearContext()
config = context.config


#Initialize logger
logging.basicConfig()
log = logging.getLogger()
log.setLevel( logging.INFO )
log.setLevel( logging.DEBUG )


#declare one required flag parameters as folder with dxm


if type(context.get_input('niftifilethree')) is dict:

    log.info("Ran 3 inputs")
    #print(three)
    path1 = context.get_input('niftifileone')['location']['path']
    path2 = context.get_input('niftifiletwo')['location']['path']
    path3 = context.get_input('niftifilethree')['location']['path']
    nifti1_title = (str(path1)[str(path1)[0:-1].rfind('/')+1:])[:(str(path1)[str(path1)[0:-1].rfind('/')+1:]).find('.')]
    log.info("The path of first nifti is " + (str(path1)))
    log.info("The path of second nifti is " + (str(path2)))
    log.info("The path of third nifti is " + (str(path3)))
    log.info("Final output will have name " + str(nifti1_title) + "_recon_ggr-w0.03.nii.gz")
    tempstr = "/flywheel/v0/output/data/"
    outputstr = "/flywheel/v0/output/recons/"
    workingstr = "/flywheel/v0/output/working/"
    os.system("mkdir " + tempstr)
    os.system("cp " + str(path1) + " " + str(path2) + " " + str(path3) + " /flywheel/v0/output/data")
    #os.system("pwd")
    #os.system("ls output/data")
    os.system("cd /flywheel/v0/output && python3 /opt/GGR-recon/preprocess.py")
    os.system("cd /flywheel/v0/output && python3 /opt/GGR-recon/recon.py --keep-negative-values --ggr -w 0.03")
    os.system("rm -rf " + tempstr)
    os.system("rm -rf " +  workingstr)
    os.system("mv recon_ggr-w0.03.nii.gz  " + str(nifti1_title) + "_recon_ggr-w0.03.nii.gz")

else:

    log.info("Ran 2 inputs")
    #print(two)
    path1 = context.get_input('niftifileone')['location']['path']
    path2 = context.get_input('niftifiletwo')['location']['path']
    nifti1_title = (str(path1)[str(path1)[0:-1].rfind('/')+1:])[:(str(path1)[str(path1)[0:-1].rfind('/')+1:]).find('.')]
    log.info("The path of first nifti is " + (str(path1)))
    log.info("The path of second nifti is " + (str(path2)))
    log.info("Final output will have name " + str(nifti1_title) + "_recon_ggr-w0.03.nii.gz")
    tempstr = "/flywheel/v0/output/data/"
    outputstr = "/flywheel/v0/output/recons/"
    workingstr = "/flywheel/v0/output/working/"
    os.system("mkdir " + tempstr)
    os.system("cp " + str(path1) + " " + str(path2) + " /flywheel/v0/output/data")
    #os.system("pwd")
    #os.system("ls output/data")
    os.system("cd /flywheel/v0/output && python3 /opt/GGR-recon/preprocess.py")
    os.system("cd /flywheel/v0/output && python3 /opt/GGR-recon/recon.py --keep-negative-values --ggr -w 0.03")
    os.system("rm -rf " + tempstr)
    os.system("rm -rf " +  workingstr)
    os.system("mv recon_ggr-w0.03.nii.gz  " + str(nifti1_title) + "recon_ggr-w0.03.nii.gz")

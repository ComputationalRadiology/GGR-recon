# Final stage of build: create a gear for Flywheel.
#FROM crkit AS crkit-gear

#Inherit  ggr-docker
FROM ggr-docker:latest AS reconstruction


#COPY --from=reconstruction
#Install additional necessary packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip vim nano zip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


RUN /usr/bin/pip3 install numpy flywheel-sdk

#Crkit
ENV BUNDLE /opt/crkit/crkit-1.6.0
ENV PATH $PATH:$BUNDLE/bin
ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:$BUNDLE/Frameworks/InsightToolkit:$BUNDLE/Frameworks/vtk-6.1:$BUNDLE/Frameworks/qt-5.3.2/lib:$BUNDLE/lib:$BUNDLE/bin
ENV QT_PLUGIN_PATH $BUNDLE/Frameworks/qt-5.3.2/plugins
ENV DYLD_LIBRARY_PATH ""

# Flywheel gear section
ENV FLYWHEEL=/flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY ggr-gear/run.py ${FLYWHEEL}/run.py
WORKDIR /flywheel/v0/output

#ENTRYPOINT ["sh", "/usr/matlab_generic_script_runner/application/run_matlab_generic_script_runner.sh", "/usr/local/MATLAB/MATLAB_Runtime/v910/","/flywheel/v0/input/iniinput.ini"]
#change entrypoint to be through fw run.py file
ENTRYPOINT ["python3", "/flywheel/v0/run.py"]

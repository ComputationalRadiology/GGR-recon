FROM ubuntu:20.04
# ENV http_proxy "http://proxy.tch.harvard.edu:3128"
ARG DEBIAN_FRONTEND=noninteractive

LABEL vendor="Computational Radiology Laboratory"
LABEL vendor="crl.med.harvard.edu"

# Update the ubuntu.
RUN apt-get -y update && \
    apt-get -y upgrade

# FIX THE MISSING LOCALE in ubuntu
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y locales \
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG=en_US.UTF-8

ENV LANGUAGE=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8 
ENV LC_TYPE=en_US.UTF-8

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y wget \
        curl vim nano zip

# install CRKIT
RUN mkdir /opt/crkit && \
        cd /opt/crkit && \
        wget http://crl.med.harvard.edu/CRKIT/CRKIT-1.6.0-RHEL6.tar.gz && \
        tar -xf CRKIT-1.6.0-RHEL6.tar.gz && \
        rm CRKIT-1.6.0-RHEL6.tar.gz

RUN apt-get install -y software-properties-common

COPY requirements.txt /tmp/requirements.txt
RUN apt-get install -y python3-pip
RUN pip3 install -r /tmp/requirements.txt

# add env variables
ENV BUNDLE /opt/crkit/crkit-1.6.0
ENV PATH $PATH:$BUNDLE/bin
ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:$BUNDLE/itk-4.6.1/lib
ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:$BUNDLE/Frameworks/InsightToolkit:$BUNDLE/Frameworks/vtk-6.1:$BUNDLE/Frameworks/qt-5.3.2/lib:$BUNDLE/lib:$BUNDLE/bin
ENV QT_PLUGIN_PATH $BUNDLE/Frameworks/qt-5.3.2/plugins
ENV DYLD_LIBRARY_PATH ""

# install GGR-recon
RUN mkdir -p /opt/GGR-recon
COPY utils.py /opt/GGR-recon
COPY preprocess.py /opt/GGR-recon
COPY recon.py /opt/GGR-recon

ENTRYPOINT cd /opt/GGR-recon && python $0 $@

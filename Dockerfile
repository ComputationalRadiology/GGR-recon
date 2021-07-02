FROM ubuntu:20.04
ENV http_proxy "http://proxy.tch.harvard.edu:3128"
ENV DEBIAN_FRONTEND=noninteractive

LABEL vendor="Computational Radiology Laboratory"
LABEL vendor="crl.med.harvard.edu"

RUN apt-get update -y && \
	apt-get install -y wget \
	curl

# install CRKIT
RUN mkdir /opt/crkit && \
	cd /opt/crkit && \
	wget http://crl.med.harvard.edu/CRKIT/CRKIT-1.6.0-RHEL6.tar.gz && \
	tar -xf CRKIT-1.6.0-RHEL6.tar.gz && \
	rm CRKIT-1.6.0-RHEL6.tar.gz

# install python3.9
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get install -y python3.9
RUN ln -s /usr/bin/python3.9 /usr/bin/python

RUN apt-get install -y python3.9-distutils

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python get-pip.py
RUN python -m pip --version

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install -r /tmp/requirements.txt

# add env variables
ENV BUNDLE /opt/crkit/crkit-1.6.0
ENV PATH $PATH:$BUNDLE/bin
ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:$BUNDLE/Frameworks/InsightToolkit:$BUNDLE/Frameworks/vtk-6.1:$BUNDLE/Frameworks/qt-5.3.2/lib:$BUNDLE/lib:$BUNDLE/bin
ENV QT_PLUGIN_PATH $BUNDLE/Frameworks/qt-5.3.2/plugins
ENV DYLD_LIBRARY_PATH ""

# install GGR-recon
RUN mkdir -p /opt/GGR-recon
COPY utils.py /opt/GGR-recon
COPY preprocess.py /opt/GGR-recon
COPY recon.py /opt/GGR-recon

ENTRYPOINT cd /opt/GGR-recon && python $0 $@

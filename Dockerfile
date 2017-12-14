FROM python:2-stretch

ENV PYTHONUNBUFFERED 1

# Install OS dependencies
# wget to retrieve SNAP
# Gdal
RUN apt update && apt install -y wget gdal-bin libgdal-dev

# Environment variables for gdal setup
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Install Snap
WORKDIR /tmp
RUN wget http://step.esa.int/downloads/5.0/installers/esa-snap_all_unix_5_0.sh
RUN chmod +x esa-snap_all_unix_5_0.sh
# Snap has prompts so we need to pass answers
RUN sh -c '/bin/echo -e "o\n1\n\n\n\ny\nn\n" | /tmp/esa-snap_all_unix_5_0.sh'
WORKDIR /usr/local/snap/bin
# Configure snappy
RUN ./snappy-conf /usr/local/bin/python /usr/local/lib/python2.7/site-packages

# Install requirements
COPY requirements.txt /requirements/
RUN pip install -r /requirements/requirements.txt
RUN mkdir -p /opt/toolkit/src

WORKDIR /opt/toolkit/src
COPY ./src /opt/toolkit/src

ENTRYPOINT ["python"]
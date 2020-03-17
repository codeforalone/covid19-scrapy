FROM openjdk:8

WORKDIR scrapy-work/

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    TZ=Asia/Tokyo \
    DEBIAN_FRONTEND=noninteractive \
    DEBCONF_NOWARNINGS=yes

#
# Development Tools
# 
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends apt-utils && \
    apt-get install -y --no-install-recommends wget && \
    apt-get install -y --no-install-recommends unzip && \
    apt-get install -y --no-install-recommends python3 && \
    apt-get install -y --no-install-recommends python3-pip

#
# PIP upgrade
#
COPY requirements.txt .
RUN pip3 install --upgrade pip setuptools wheel && \
    pip3 install -r requirements.txt && \
    echo "*** INSTALLED: python modules ***"

WORKDIR /tools

CMD ["bash", "build_data.sh"]

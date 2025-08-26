FROM  --platform=linux/amd64 python:3.11

# Install system dependencies for geospatial packages
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    libspatialindex-dev \
    build-essential \
    pkg-config \
    htop \
    procps \
    findutils \
    iftop \
    iptables \
    iproute2 \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV GDAL_CONFIG=/usr/bin/gdal-config
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Upgrade pip and install wheel
RUN pip install --upgrade pip setuptools wheel

# Install Cython first (required for some geospatial packages)
RUN pip install Cython
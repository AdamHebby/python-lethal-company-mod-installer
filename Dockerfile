FROM cdrx/pyinstaller-windows:python3

RUN apt-get update -y && \
    apt-get install -y wget && \
    pip install pyinstaller-versionfile


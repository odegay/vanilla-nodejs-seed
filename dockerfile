FROM ubuntu:latest
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    jq \
    curl \
    git
VOLUME [ "/data" ]
WORKDIR /data
ENTRYPOINT ["/bin/bash"]

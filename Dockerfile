# kics-scan disable=fd54f200-402c-4333-a5a4-36ef6709af2f
# Bitbucket requires the container to run as "root" in order to write to the storage directory:
# https://community.atlassian.com/forums/Bitbucket-questions/Is-a-pipe-running-in-a-Docker-image-without-root-user-supported/qaq-p/2833653

# RUN groupadd -r pipe && useradd -r -g pipe pipe && \
#   mkdir /home/pipe && chown pipe:pipe /home/pipe && \
#   mkdir /workspace && chown pipe:pipe /workspace
# USER pipe

FROM python:3.13-slim
LABEL maintainer="CyberArk Software Ltd."

RUN mkdir /workspace

# install requirements
COPY requirements.txt /workspace
WORKDIR /workspace
RUN pip install --no-cache-dir -r requirements.txt

# copy the pipe source code
# TODO: For dev, use a mount instead of copying the files (or document how to open VS Code in container)
COPY LICENSE README.md pipe.yml /workspace/
COPY pipe /workspace/pipe

ENTRYPOINT ["python3", "/workspace/pipe/pipe.py"]

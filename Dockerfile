FROM python:3-slim
LABEL maintainer="CyberArk Software Ltd."

RUN groupadd -r pipe && useradd -r -g pipe pipe && \
  mkdir /home/pipe && chown pipe:pipe /home/pipe && \
  mkdir /workspace && chown pipe:pipe /workspace
USER pipe

# install requirements
COPY requirements.txt /workspace
WORKDIR /workspace
RUN pip install --no-cache-dir -r requirements.txt

# copy the pipe source code
# TODO: For dev, use a mount instead of copying the files (or document how to open VS Code in container)
COPY LICENSE README.md pipe.yml /workspace/
COPY pipe /workspace/pipe

ENTRYPOINT ["python3", "/workspace/pipe/pipe.py"]

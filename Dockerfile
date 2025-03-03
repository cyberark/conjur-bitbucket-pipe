FROM python:3.10-slim
LABEL maintainer="CyberArk Software Ltd."

RUN groupadd -r pipe && useradd -r -g pipe pipe
RUN mkdir /home/pipe
RUN chown pipe:pipe /home/pipe
USER pipe

# install requirements
COPY requirements.txt /home/pipe
WORKDIR /home/pipe
RUN pip install --no-cache-dir -r requirements.txt

# copy the pipe source code
# TODO: For dev, use a mount instead of copying the files (or document how to open VS Code in container)
COPY pipe /home/pipe/
COPY LICENSE README.md pipe.yml /home/pipe/

ENTRYPOINT ["python3", "/home/pipe/pipe.py"]

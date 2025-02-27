FROM python:3.10-slim
LABEL maintainer="CyberArk Software Ltd."

# install requirements
COPY requirements.txt /
WORKDIR /
RUN pip install --no-cache-dir -r requirements.txt

# copy the pipe source code
# TODO: For dev, use a mount instead of copying the files (or document how to open VS Code in container)
COPY pipe /
COPY LICENSE README.md pipe.yml /

ENTRYPOINT ["python3", "/pipe.py"]

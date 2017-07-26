FROM python:3.5-alpine

LABEL MAINTAINER digital.innovation@infinitus-int.com

# setup env
ENV APP_DIR /usr/src/app

RUN set -x && \
    mkdir -p ${APP_DIR}

WORKDIR ${APP_DIR}

COPY requirements.txt *.py ./
RUN chmod +x chaos.py && \
    pip3 install --no-cache-dir -r requirements.txt

CMD ["./chaos.py"]
FROM python:3.10-alpine

# TODO Once the pandoc package makes it to stable, fetch it from there
RUN apk update && apk add git && apk add pandoc --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY main.py /main.py

ENTRYPOINT ["python3"]
CMD ["/main.py"]

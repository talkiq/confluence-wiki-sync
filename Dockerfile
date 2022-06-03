FROM python:3.13-slim-bullseye

RUN apt-get update && apt-get install git pandoc -y

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY *.py /

ENTRYPOINT ["python3"]
CMD ["/wiki_sync.py"]

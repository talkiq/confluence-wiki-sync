FROM python:3.9-bullseye

# TODO Once the pandoc package makes it to stable, fetch it from there
RUN apt-get update && apt-get install pandoc -y

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY wiki_sync.py /wiki_sync.py

ENTRYPOINT ["python3"]
CMD ["/wiki_sync.py"]

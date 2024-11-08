# When updating the image, remember to make the same update in the CircleCI config
FROM python:3.13-slim

RUN apt-get update && apt-get install pandoc -y

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY *.py /

ENTRYPOINT ["python3"]
CMD ["/wiki_sync.py"]

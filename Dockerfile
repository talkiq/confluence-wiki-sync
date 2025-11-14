# When updating the image, remember to make the same update in the CircleCI config
FROM python:3.14-slim

ENV INSTALL_DIR="/app"
RUN mkdir -p $INSTALL_DIR/pandoc_filters

WORKDIR $INSTALL_DIR

RUN apt-get update && apt-get install pandoc -y

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY *.py .
COPY pandoc_filters/*.lua ./pandoc_filters/

ENTRYPOINT ["python3"]
CMD ["/app/wiki_sync.py"]

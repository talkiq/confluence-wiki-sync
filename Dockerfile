# When updating the image, remember to make the same update in the CircleCI config
FROM python:3.14-slim

ENV INSTALL_DIR="/app"
RUN mkdir -p $INSTALL_DIR/pandoc_filters

RUN apt-get update && apt-get install pandoc -y

COPY *.py $INSTALL_DIR
COPY requirements.txt $INSTALL_DIR
COPY pandoc_filters/*.lua $INSTALL_DIR/pandoc_filters/

WORKDIR $INSTALL_DIR

RUN pip install -r requirements.txt

ENTRYPOINT ["python3"]
CMD ["/app/wiki_sync.py"]

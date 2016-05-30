FROM python:2.7
MAINTAINER benjaminrk@gmail.com
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
ADD watch.py watch.py
USER nobody
ENTRYPOINT [ "python", "watch.py" ]

FROM ubuntu
MAINTAINER oleg_kuzmin

ENV REFRESHED_AT 2016–05-05

RUN echo "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) main universe" >> /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y nginx python python-dev python-setuptools git
RUN easy_install pip
RUN pip install uwsgi

COPY /src /home/owl-pub
COPY /configs/nginx.conf /etc/nginx/nginx.conf
COPY /configs/uwsgi_params /etc/nginx/uwsgi_params
COPY /ssl-certificates/* /etc/nginx/_ssl/
COPY /configs/config.json /home/owl-pub/config.json

RUN pip install -r /home/owl-pub/requirements.txt

EXPOSE 80

WORKDIR /home/owl-pub

CMD python OwlPub.py && service nginx start && uwsgi owl-pub.ini

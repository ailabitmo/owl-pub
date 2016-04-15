FROM ubuntu
MAINTAINER oleg_kuzmin

ENV REFRESHED_AT 2016–04–15

RUN echo "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) main universe" >> /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y nginx python python-dev python-setuptools git
RUN easy_install pip
RUN pip install uwsgi

ADD / /home/owl-pub
ADD /nginx/nginx.conf /etc/nginx/nginx.conf
ADD /nginx/uwsgi_params /etc/nginx/uwsgi_params

RUN pip install -r /home/owl-pub/src/requirements.txt

EXPOSE 80 443

WORKDIR /home/owl-pub/src

CMD python OwlPub.py && service nginx start && uwsgi owl-pub.ini

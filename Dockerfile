FROM ubuntu
MAINTAINER oleg_kuzmin

RUN echo "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) main universe" >> /etc/apt/sources.list
RUN apt-get update

RUN apt-get install -y  nginx python python-dev python-setuptools git
RUN easy_install pip
RUN pip install uwsgi

ADD /owlpub /home/owlpub
ADD /uwsgi/owl-pub.ini /home/owlpub/owlpub.ini
ADD /nginx/nginx.conf /etc/nginx/nginx.conf
ADD /nginx/mime.types /etc/nginx/mime.types
ADD /nginx/uwsgi_params /etc/nginx/uwsgi_params
ADD /nginx/default /etc/nginx/sites-available/default
RUN pip install -r /home/owlpub/requirements.txt

EXPOSE 80

WORKDIR /home/owlpub

CMD  python OwlPub.py && service nginx start && uwsgi owlpub.ini

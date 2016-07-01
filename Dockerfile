FROM ubuntu

#RUN echo "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) main universe" >> /etc/apt/sources.list
RUN apt-get update && \
  apt-get install -y nginx python3 python3-pip uwsgi uwsgi-plugin-python3 git

COPY /src /home/owl-pub

RUN pip3 install -r /home/owl-pub/requirements.txt

COPY /configs/config.json /home/owl-pub/config.json
COPY /configs/nginx.conf /etc/nginx/nginx.conf
COPY /configs/uwsgi_params /etc/nginx/uwsgi_params
COPY /ssl-certificates/* /etc/nginx/_ssl/
COPY /custom_templates /home/owl-pub/custom_templates

EXPOSE 80 443

WORKDIR /home/owl-pub

CMD python3 OwlPub.py && service nginx restart && uwsgi owl-pub.ini

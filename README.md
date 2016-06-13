# OWL-Pub  
A framework for publishing and managing OWL ontologies

# Installation using a Docker
#####1. Clone
```bash
git clone https://github.com/ailabitmo/owl-pub.git && cd owl-pub
```

#####2. Prepare configs
######a. For HTTP setup:
```bash
cp examples/nginx.conf configs/nginx.conf
```
######b. For HTTPS setup:
```bash
cp examples/nginx-ssl.conf configs/nginx.conf
```
Also you must place two files ssl_certificate named fullchain.pem and 
        ssl_certificate_key named privkey.pem in  "ssl-certificates" directory.
######c. Common:
```bash
editor configs/nginx.conf
cp examples/config.json configs/config.json
editor configs/config.json
```

#####3. Build & run
Note: replace `8000` port you want
```
docker build -t owl-pub:last
docker run -p 127.0.0.1:8000:80 -i -t owl-pub:last
```

# TODO:
 * Fix custom templates static files serving problem
 * Fix documentation
  
# Related work  
 * [Live OWL Documentation Environment (LODE)](http://www.essepuntato.it/lode)  
 * [Parrot: a RIF and OWL documentation service](http://ontorule-project.eu/parrot/parrot)  
 * [OWLDoc](http://neon-toolkit.org/wiki/OWLDoc)  
 * [OntoSpec](http://home.mis.u-picardie.fr/~site-ic/site/)  
 * [Neologism](neologism.deri.ie)
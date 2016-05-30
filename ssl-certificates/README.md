This file is needed because of an [issue 13045](https://github.com/docker/docker/issues/13045): using wildcards like "COPY foo/* bar/" not work if no file in foo.

Place here two files for HTTPS setup: 
* ssl_certificate (named fullchain.pem for nginx-ssl.conf example config);
* ssl_certificate_key named privkey.pem (named fullchain.pem for nginx-ssl.conf example config).
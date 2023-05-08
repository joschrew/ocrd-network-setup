This is to test the Processing-Server (remote or locally)
- purpose of this manual is running it on my own local machine, this is not meant to be an
  instruction usable by everyone out of the box

Run the webapi an processing-server locally:
- run processing-server simply from the github repo:
    - zi core
    - systemctl start sshd
    - python3.8 -m venv venv
    - . venv/bin/activate.fish
    - # git pull origin processor-server
    - # make install-dev
    - # vim ocrd_network/ocrd_network/processing_server.py
    - # from pudb import set_trace; set_trace()
    - ocrd processing-server test-configs/my-test-config.yml -a localhost:8080

- then start webapi with docker:
    - zi setup/examples
    - # docker-compose build --no-cache
    - # mkdir -p /tmp/ocrd-webapi-data-test
    - docker-compose up -d

- additionally test a processor (e.g. ocrd-cis-ocropy-binarize):
    - # clone: `zi githubclones` `git clone git clone https://github.com/cisocrgroup/ocrd_cis.git ocrd_cis`
    - zi core
    - . venv/bin/activate.fish
    - zi ocrd_cis
    - make install-devel # other processor probably have to be installed differently

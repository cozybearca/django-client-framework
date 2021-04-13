FROM ubuntu

RUN apt-get update
RUN apt-get install -y python3-pip
RUN apt-get install -y git
RUN apt-get install -y curl
RUN apt-get install -y wait-for-it
RUN apt-get install -y tar

RUN curl -fsSL https://deb.nodesource.com/setup_15.x | bash -
RUN apt-get install -y nodejs
RUN npm install --global yarn

COPY ./requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

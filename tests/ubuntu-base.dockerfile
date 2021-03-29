FROM ubuntu

RUN apt-get update
RUN apt-get install -y python3-pip
RUN apt-get install -y git
RUN apt-get install -y curl
RUN apt-get install -y wait-for-it

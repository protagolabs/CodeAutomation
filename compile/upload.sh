set -e
set -x
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 134622832812.dkr.ecr.us-west-2.amazonaws.com
docker build -t nuitka-build .
docker tag nuitka-build:latest 134622832812.dkr.ecr.us-west-2.amazonaws.com/nuitka-build:latest
docker push 134622832812.dkr.ecr.us-west-2.amazonaws.com/nuitka-build:latest




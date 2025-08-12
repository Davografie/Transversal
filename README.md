# installation
*tested on Ubuntu 24.04 LTS*

## requirements
### Linux
- docker
- docker-compose
see https://docs.docker.com/compose/install/

### Windows
- docker desktop (needs to be running)

## steps
### download/clone this repository

### download and extract media
The media folder contains all images for the starting locations. You can also choose to upload your own pictures instead. To use the preset images, download the media.zip file and put the unzipped media folder in the root folder of this project.

### configure .env
Change the IP in the .env file to the address you want it accessible on (either your public IP or local IP).

Then create port forwarding in your router for ports 8080, 8529, and 5000 if you want to have it accessible over the internet.

Change the media folder in the .env file to the directory where you saved this folder, appended with `/media`.

### build the server
Navigate to the project root folder in terminal. On Windows you can first go to the root folder, right-click and click "Open in Terminal".
```
docker compose up -d --build
```

### load initial database
Only required on first run.

Access the docker container with this line:
```
docker exec -it tv_adb sh
```

Then load the initial database with this command (replace password if changed in .env):
```
arangorestore \
  --input-directory /init_data \
  --server.endpoint tcp://127.0.0.1:8529 \
  --server.username root \
  --server.database transversal \
  --create-database true \
  --server.password somepassword
```

### run the server
In terminal from the root of the project folder:
```
docker compose up -d
```

### access the service
from any browser visit the entered IP-address with port :8080

# message from the developer
*This is my first public repo. You can create bug reports, pull requests, etc. but I'm going to need some time to figure out how to handle those.*

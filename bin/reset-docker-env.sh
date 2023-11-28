
# stop and remove containers
docker stop $(docker ps -aq)
docker remove $(docker ps -aq)

# clean system env, storage, etc
docker system prune -f

# clear volume set-up
docker volume rm $(docker volume ls | grep -v VOLUME | awk '{print $2}')

# clear network set-up
docker network rm $(docker network ls | awk '{print $2}')

# show current status
echo ========= IMAGES =========
docker images

echo ========= CONTAINERS =========
docker ps

echo ========= VOLUMES =========
docker volume ls

echo ========= NETWORK =========
docker network ls

# build all images
source ./bin/build-all.sh
echo "Done"

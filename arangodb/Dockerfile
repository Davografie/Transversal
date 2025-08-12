# docker/arangodb/Dockerfile
FROM arangodb:3.8.0

# Copy initialization files
COPY ./init_data /var/lib/arangodb3/dumps/initial

# Ensure proper permissions
# RUN chmod -R 755 /var/lib/arangodb3/dumps/initial

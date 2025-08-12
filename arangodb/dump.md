Source: DeepSeek

Since the `arangodb` Docker image is based on a minimal Linux distribution (Alpine) and doesn’t include `bash`, you’ll need to use `sh` instead. Here’s how to safely dump/restore your database and handle your feature branch workflow:

---

### **1. Access the ArangoDB Container Shell**
Use `sh` (not `bash`):
```bash
docker exec -it your_arangodb_container_name sh
```

---

### **2. Create a Backup with `arangodump`**
Run this inside the container:
```bash
arangodump \
  --output-directory /tmp/arangodb_dump \
  --server.endpoint tcp://127.0.0.1:8529 \
  --server.username root \
  --server.password your_root_password \
  --overwrite true
```
Replace `your_root_password` with your actual root password (or use a user with backup privileges).  
This saves the dump to `/tmp/arangodb_dump` in the container.

---

### **3. Copy the Dump to Your Host Machine**
From your host terminal (not inside the container):
```bash
docker cp your_arangodb_container_name:/tmp/arangodb_dump ./arangodb_dump
```
This copies the dump to `./arangodb_dump` on your host.

---

### **4. Restore the Dump to a New Database (Feature Branch)**
#### **Option A: Restore to the Same Container (New Database)**
1. Create a new database (e.g., `feature_branch`) via ArangoDB web interface or `arangosh`.
2. Restore the dump:
   ```bash
   arangorestore \
     --input-directory /tmp/arangodb_dump \
     --server.endpoint tcp://127.0.0.1:8529 \
     --server.username root \
     --server.password your_root_password \
     --create-database true \
     --database feature_branch
   ```

#### **Option B: Spin Up a New Container for Isolation**
1. Start a new ArangoDB container with a fresh volume:
   ```bash
   docker run -d --name arangodb_feature \
     -v arangodb_feature_data:/var/lib/arangodb3 \
     -p 8529:8529 \
     arangodb
   ```
2. Copy the dump to the new container:
   ```bash
   docker cp ./arangodb_dump arangodb_feature:/tmp/arangodb_dump
   ```
3. Restore the dump:
   ```bash
   docker exec -it arangodb_feature sh -c "arangorestore \
     --input-directory /tmp/arangodb_dump \
     --server.endpoint tcp://127.0.0.1:8529 \
     --server.username root \
     --server.password '' \
     --overwrite true"
   ```

---

### **5. Develop Your Feature Branch**
- Modify the `feature_branch` database (e.g., update dice ratings from `['d4', 'd6', 'd8']` to `[-1, 2, 3]`).
- Test your changes in isolation.

---

### **6. Discard or Merge Changes**
#### **To Discard:**
Stop and remove the feature container/volume:
```bash
docker stop arangodb_feature && docker rm arangodb_feature
docker volume rm arangodb_feature_data
```

#### **To Merge:**
1. Dump the modified data from the feature branch:
   ```bash
   arangodump \
     --output-directory /tmp/arangodb_feature_dump \
     --server.endpoint tcp://127.0.0.1:8529 \
     --server.username root \
     --server.password your_root_password \
     --database feature_branch
   ```
2. Restore to the main database (use `--overwrite true` cautiously!).

---

### **Key Notes**
- **Why `sh`?** Alpine Linux (used by ArangoDB’s image) doesn’t include `bash` by default.
- **Docker Volumes**: Avoid manual copies of `/var/lib/docker/volumes/...`—it risks corruption.
- **Init Scripts**: To automate restores on container startup, place dumps in `/docker-entrypoint-initdb.d/` (per Docker Hub docs).

---

### **Example: Automated Restore via Docker Entrypoint**
1. Place your dump in `./arangodb_dump` on your host.
2. Mount it to `/docker-entrypoint-initdb.d/` in a new container:
   ```bash
   docker run -d --name arangodb_feature \
     -v $(pwd)/arangodb_dump:/docker-entrypoint-initdb.d/arangodb_dump \
     -p 8529:8529 \
     arangodb
   ```
   The container will automatically restore the dump on startup.

This approach keeps your main data safe while allowing isolated development.

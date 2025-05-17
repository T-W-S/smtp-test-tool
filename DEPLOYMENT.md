# SMTP Tool Docker Deployment

## Quick Setup

1. Extract the archive:
   ```bash
   tar -xzvf smtp-tool.tar.gz
   mkdir -p smtp-tool
   mv * smtp-tool/
   cd smtp-tool
   ```

2. Build and run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Access the application at http://your-server-ip:5000

## Configuration

The application stores all settings, profiles, and logs in a Docker volume named `smtp-tool-data` for persistence.

## Updating

To update the application:
1. Extract the new version
2. Run `docker-compose down`
3. Run `docker-compose up -d --build`

Your saved data will be preserved in the volume.


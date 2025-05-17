# SMTP Tool Docker Deployment Update

## Quick Setup for Updated Version

1. Extract the archive:
   ```bash
   tar -xzvf smtp-tool-update.tar.gz
   cd smtp-tool-update
   ```

2. Stop the existing container:
   ```bash
   docker-compose down
   ```

3. Build and run with Docker Compose:
   ```bash
   docker-compose up -d --build
   ```

4. Access the application at http://your-server-ip:5000

## Changes in this Update

1. Fixed issue with duplicate email sending
   - Reduced workers to 1 to prevent race conditions
   - Increased duplicate detection window from 3 to 10 seconds

2. Added persistent SMTP logging
   - SMTP logs are now stored in a dedicated volume
   - Logs can be found in the 'smtp-tool-logs' Docker volume

Your saved settings, profiles, and email history will be preserved during the update.


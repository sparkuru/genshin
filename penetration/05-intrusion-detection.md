# intrusion-detection

1. ps

   ```bash
   ps aux --sort=-%cpu | head -n 20
   ps aux --sort=-%mem | head -n 20
   ```

2. network

   ```bash
   sudo netstat -tulnp
   sudo ss -tulnp
   lsof -i :<port>
   ```

3. journalctl

   ```bash
   journalctl -b -1 -r
   ```

4. cron

   ```bash
   crontab -l
   sudo cat /etc/crontab
   sudo ls /etc/cron.*
   ```

5. other

   ```bash
   sudo apt install rkhunter chkrootkit
   sudo rkhunter --check
   sudo chkrootkit
   ```
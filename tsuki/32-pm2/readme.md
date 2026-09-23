
https://pm2.keymetrics.io/

```bash
./install-pm2.sh --path "/path/to/portable/pm2/dir"
source "$HOME/.local/share/portable-pm2/env.sh"

pm2 start app.js
pm2 save
pm2 startup
```
唐。制作 static 的 telnet 服务端

## setup telnet in apt

1. `sudo apt install xinetd telnetd`

2. 执行

   ```bash
   cat << EOL > /etc/xinetd.conf
   # Simple configuration file for xinetd
   #
   # Some defaults, and include /etc/xinetd.d/
   
   defaults
   {
   
   # Please note that you need a log_type line to be able to use log_on_success
   # and log_on_failure. The default is the following :
   # log_type = SYSLOG daemon info
   instances = 60
   log_type = SYSLOG authpriv
   log_on_success = HOST PID
   log_on_failure = HOST
   cps = 25 30
   
   }
   
   includedir /etc/xinetd.d
   EOL
   
   cat << EOL > /etc/xinetd.d/telnet
   # default: on
   # description: The telnet server serves telnet sessions; it uses \
   # unencrypted username/password pairs for authentication.
   service telnet
   {
   disable = no
   flags = REUSE
   socket_type = stream
   wait = no
   user = root
   server = /usr/sbin/in.telnetd
   log_on_failure += USERID
   }
   EOL
   ```

3. 启动 telnet：`sudo /etc/init.d/xinetd restart`

## refer

1. https://jun-wang.gitbook.io/learnjava/kai-fa/huan-jing-da-jian/ubuntu-kai-qi-telnet
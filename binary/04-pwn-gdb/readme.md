# gdb

1. pwndbg env

   1. `.gdbinit`
   2. tmux，https://gist.github.com/ryerh/14b7c24dfd623ef8edc7
   3. heap angel

2. gdb tracing error

   ```bash
   $ gdb elf
   (gdb) run -c config.json
   Starting program: /tmp/elf -c config.json
   Server started on 127.0.0.1:8080
   
   Thread 2 "elf" received signal SIGSEGV, Segmentation fault.
   [Switching to Thread 0x7ffff7ff86c0 (LWP 1060)]
   0x000000000040563f in get_object_item ()
   (gdb) bt
   #0  0x000000000040563f in get_object_item ()
   #1  0x000000000040569f in cJSON_GetObjectItem ()
   #2  0x0000000000401e3f in find_register_by_address ()
   #3  0x0000000000402046 in handle_request ()
   #4  0x00000000004023a5 in server_thread ()
   #5  0x000000000042598f in start_thread ()
   #6  0x0000000000446fd8 in __clone3 ()
   ```

   打印 stack trace，定位问题

3. 


## refer

1. 
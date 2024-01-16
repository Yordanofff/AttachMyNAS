<h1 align="center">Attach My NAS</h1>
<p align="center">A Windows System Tray Application that will simplify connection to a Network Attached Storage devices </p>
<hr>

## What is it good for?

-   When you want to connect easily to multiple NAS drives (Home,Work,Friends...)
-   When you want to connect using diffferent credentials to your nas (RO account, RW account, etc..)
-   When you don't want your NAS to be always connected. Easy ON/OFF
  
<hr>

You can add as many 'configs' and 'shares' as you wish and they'll show up in the System Tray app.
'letters' is optional and if any are missing the app will use the last free Drive letter on the system - Z, Y, X... 

```
[Home-NAS-RW]
ip = 192.168.1.100  # IP or a Hostname
username = home_user_rw
password = home_user_pw123
shares = Movies, Downloads, Games  # Comma-separated shares on the server
letters = M, D, G # [Optional] - Comma-separated preferred letters for the shares above. Position can
# be blank too ",L,M" in which case Movies will be assigned to drive 'Z' (or the last free letter)
```

<hr>

Preffered way to edit the config file is from the app. It will monitor for a change in the file and will restart the app automatically if a change has been made.
![image](https://github.com/Yordanofff/AttachMyNAS/assets/57867535/53cb6367-053f-466b-9128-3c1b7210341c)

-  Unmount All [PC] - will unmount all network drives on the PC. 
-  Unmount All [Config] - will unmount all network drives that are connected to any IP from the config file.
-  Restart - will restart the app in case you've edited the config file manually.

![image](https://github.com/Yordanofff/AttachMyNAS/assets/57867535/4b2d07b5-a6f6-427d-8b58-24d960d80bc4)

-  There is an option to mount/unmount all shares in each group too.
-  [None] means that there isn't a preffered letter for 'Books' and the system will use the last free letter.

# Secure your SSH server

An SSH connection is kind of like a fire: it needs three ingredients in order to survive.
Take any one of those three away, and the whole thing ceases to be.
In the case of a remote SSH server, any user can connect to it as long as they have the following three bits of data:

1. Username
2. Password
3. The port SSH is using

Remove any of those three and the server becomes infinitely more secure from brute-force style attacks.
Sometimes these can originate from the other side of the planet (which is kind of neat).

![hong kong](/images/hongkong.png)

If your currently running a machine that hosts an SSH server, run the following command to see if your machine is being targeted.
Here’s an example of what happens to the machine hosting this website roughly every minute.

	grep ‘Invalid’ /var/log/auth.log

	Invalid user iroda from 101.32.181.50 port 36710
	Invalid user frank from 49.232.174.23 port 39118
	Invalid user egon from 45.240.88.142 port 39456
	Invalid user squirrel from 59.152.237.118 port 54674
	Invalid user dragos from 129.211.16.182 port 34308
	Invalid user miroslav from 128.199.216.49 port 44258
	Invalid user admin from 144.34.170.120 port 58604
	Invalid user visiteur from 59.152.237.118 port 46436
	Invalid user aaaaa from 103.212.120.87 port 58578

This kind of attack is especially effective on machines with default parameters such as `admin` and `password`, or in the case of default raspberry pis, `pi` and `rapsberry`.
Clearly, there are a LOT Of machines attempting to beat down the door and get inside.
As you can see, none of them really have a clue as to which username or port to specify, almost every connection attempt is effectively throwing data at a wall and hoping something will stick.
Eventually, given enough time, something might.
Thankfully, you can have peace of mind by following a few of these simple steps.

Instead of using a password every time you log into your machine remotely, consider using an SSH key instead.
This removes the possibility (however incredibly unlikely) that one of these machines might guess your password.

    ssh-keygen

After the key is created on your local machine, copy it to your remote machine.

    ssh-copy-id username@domain_name

Once the server has your home machine’s key, you can remove the ability to log in via a password.
Be warned though, if you lose your key on your local machine for whatever reason you won’t be able to get back into your remote server.
Because of this, I would recommend that newer users have a [complicated password](http://password-checker.online-domain-tools.com/) as a backup in addition to an SSH key in the case of an emergency.

By default, SSH communicates using port 22.
One of the best ways to secure your connection is to change it.
Pick an alternate one to use, but be aware that a lot of ports are already [used by other services](https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers#Well-known_ports).

Once you’ve picked one out, edit `/etc/ssh/sshd_config` and modify the following lines:

	Port $your_port
	PermitRootLogin no
    MaxAuthTries 3
    PubkeyAuthentication yes
    AllowUsers username
    PasswordAuthentication no (or yes, if that’s what you want)
    PermitEmptyPasswords no
    PrintLastLog yes

### Ban the intruders

Now that all three connection requirements have been secured, it’s important to be able to ban the IP addresses who are attempting brute force attacks.

	apt install fail2ban

Once it's installed, copy the default conf file to a local one.

    cp /etc/fail2ban/jail.{conf,local}

Edit the newly created local file and remove everything except for the `[sshd]` section.

	vim /etc/fail2ban/jail.local
	
	[sshd]
	
	enabled = true
	port    = ssh
	maxretry = 3
	findtime = 10m
	bantime = 24h
	logpath = %(sshd_log)s
	backend = %(sshd_backend)s

Restart the service and double check that it’s working correctly

	systemctl restart fail2ban
	systemctl status fail2ban

After a few hours, run `grep 'banned' /var/log/fail2ban.log` to see the fruits of it's labor.

    WARNING [sshd] 217.93.169.142 already banned
    WARNING [sshd] 18.209.187.21 already banned
    WARNING [sshd] 116.59.25.196 already banned
    WARNING [sshd] 59.152.237.118 already banned
    WARNING [sshd] 153.36.233.60 already banned
    WARNING [sshd] 114.141.167.190 already banned

### Set up a firewall

ufw is a firewall application for linux.
By blocking all other ports except for the ones you are using, you help reduce the vector of attacks from the outside.

	apt install ufw
	enable ufw
    
	ufw allow $your_port

check that it’s running correctly

	ufw status

And there you have it!
Your server should be a lot more secure now.
Remember to periodically check logs and monitor your server to keep it healthy and happy.
#!/bin/bash
# This is a GCE startup script for Memes as a Service codelab.

GAE_VERSION='1.8.4'
ID=`uname -n`

# Installs dependencies
apt-get install -y gcc ed zip git-core python-imaging emacs23-nox vim tmux

# Downloads App Engine SDK
rm -f /tmp/google_appengine_${GAE_VERSION}.zip
rm -f /usr/local/google_appengine
cd /tmp
wget https://googleappengine.googlecode.com/files/google_appengine_${GAE_VERSION}.zip
cd /usr/local
unzip -q /tmp/google_appengine_${GAE_VERSION}.zip
rm -f /tmp/google_appengine_${GAE_VERSION}.zip

# Adds preferred settings
cat >> /etc/skel/.vimrc <<EOF
set expandtab
set tabstop=4
set shiftwidth=4
set autoindent
set smartindent
syntax on
EOF

# Adds tmux configuration
cat >> /etc/skel/.tmux.conf <<EOF
set-option -g prefix C-o
unbind C-b
set-window-option -g utf8 on
set-option -g default-command \$SHELL
EOF

# Adds PATH and aliases to .bashrc
cat >> /etc/skel/.bashrc <<EOF
export PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/google_appengine
alias dev_appserver.py="dev_appserver.py --host 0.0.0.0 --admin_host 0.0.0.0"
alias appcfg.py="appcfg.py --oauth2 --noauth_local_webserver"
EOF

# Disables password auth for ssh and clones the repo upon login.
cat >> /etc/skel/.profile <<EOF
/usr/local/bin/bansshpasswd
if [ ! -d "\${HOME}/appengine-codelab-maas-python" ] ; then
    git clone https://github.com/GoogleCloudPlatform/appengine-codelab-maas-python.git
fi
cd \${HOME}/appengine-codelab-maas-python
EOF

# Removes attendees secrets, and turns on password login for ssh.
cat >> /etc/skel/.bash_logout <<EOF
shred -n 200 -z -u \${HOME}/.appcfg_oauth2_tokens
/usr/local/bin/opensshpasswd
EOF

# Remove and add the user
userdel -f -r $ID
useradd -m $ID -k /etc/skel -s /bin/bash
passwd $ID <<EOF
$ID
$ID
EOF

# Turns on the password authentication.
cp /etc/ssh/sshd_config /etc/ssh/.sshd_config.org
ed /etc/ssh/sshd_config <<EOF
/PasswordAuthentication no/s/ no/ yes/
w
q
EOF
cp /etc/ssh/sshd_config /etc/ssh/.sshd_config.passwd

# Creates 2 root suid binaries for turn on/off password authentication
cd /tmp

cat <<EOF > /tmp/bansshpasswd.c
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

int main()
{
   setuid( 0 );
   system("/bin/cp /etc/ssh/.sshd_config.org /etc/ssh/sshd_config");
   system("/usr/sbin/service ssh restart");

   return 0;
}
EOF

gcc bansshpasswd.c -o bansshpasswd
mv bansshpasswd /usr/local/bin
chmod 4755 /usr/local/bin/bansshpasswd
rm bansshpasswd.c

cat <<EOF > /tmp/opensshpasswd.c
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

int main()
{
   setuid( 0 );
   system("/bin/cp /etc/ssh/.sshd_config.passwd /etc/ssh/sshd_config");
   system("/usr/sbin/service ssh restart");

   return 0;
}
EOF

gcc opensshpasswd.c -o opensshpasswd
mv opensshpasswd /usr/local/bin
chmod 4755 /usr/local/bin/opensshpasswd
rm opensshpasswd.c

# Restarts ssh for password auth.
service ssh restart

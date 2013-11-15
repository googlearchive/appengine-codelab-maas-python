#!/bin/bash
# This is a GCE startup script for Memes as a Service codelab.

GAE_VERSION='1.8.7'
ID=`uname -n`
PASSWD='' # you need to specify

# Installs dependencies
apt-get install -y gcc ed zip git-core python-imaging emacs23-nox vim tmux

# Downloads App Engine SDK
rm -f /tmp/google_appengine_${GAE_VERSION}.zip
rm -f /usr/local/google_appengine
cd /tmp
wget http://commondatastorage.googleapis.com/maas-codelab/google_appengine_${GAE_VERSION}.zip
wget http://commondatastorage.googleapis.com/maas-codelab/appengine-codelab-maas-python.zip

cd /usr/local
unzip -q /tmp/google_appengine_${GAE_VERSION}.zip
rm -f /tmp/google_appengine_${GAE_VERSION}.zip
unzip -q /tmp/appengine-codelab-maas-python.zip
rm -f /tmp/appengine-codelab-maas-python.zip

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

# Clones the repo upon login.
cat >> /etc/skel/.profile <<EOF
if [ ! -d "\${HOME}/appengine-codelab-maas-python" ] ; then
    git clone /usr/local/appengine-codelab-maas-python \${HOME}/appengine-codelab-maas-python
fi
cd \${HOME}/appengine-codelab-maas-python
EOF

# Removes attendees secrets upon logout
cat >> /etc/skel/.bash_logout <<EOF
shred -n 200 -z -u \${HOME}/.appcfg_oauth2_tokens
EOF

# Remove and add the user
userdel -f -r $ID
useradd -m $ID -k /etc/skel -s /bin/bash
passwd $ID <<EOF
$PASSWD
$PASSWD
EOF
chage -d 0 $ID

# Turns on the password authentication.
ed /etc/ssh/sshd_config <<EOF
/PasswordAuthentication no/s/ no/ yes/
w
q
EOF

# Restarts ssh for password auth.
service ssh restart

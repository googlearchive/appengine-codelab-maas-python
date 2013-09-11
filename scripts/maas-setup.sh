#!/bin/bash

GAE_VERSION='1.8.4'
DIRECTORY=maas
cd ${HOME}
if [ -d "$DIRECTORY" ]; then
  echo "Directory $DIRECTORY exists. Exiting."
  exit 1
fi
mkdir $DIRECTORY
cd $DIRECTORY
sudo apt-get install -y zip git-core python-imaging emacs23-nox vim tmux
wget https://googleappengine.googlecode.com/files/google_appengine_${GAE_VERSION}.zip
unzip -q google_appengine_${GAE_VERSION}.zip
export PATH=${PATH}:${HOME}/${DIRECTORY}/google_appengine
alias dev_appserver.py="dev_appserver.py --host 0.0.0.0 --admin_host 0.0.0.0"
alias appcfg.py="appcfg.py --oauth2 --noauth_local_webserver"
git clone https://github.com/GoogleCloudPlatform/appengine-codelab-maas-python.git
cd appengine-codelab-maas-python

read -p "Do you want me to modify your dot files? " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
  exit 0
fi

cat >> ${HOME}/.vimrc <<EOF
set expandtab
set tabstop=4
set shiftwidth=4
set autoindent
set smartindent
syntax on
EOF

cat >> ${HOME}/.tmux.conf <<EOF
set-option -g prefix C-o
unbind C-b
set-window-option -g utf8 on
set-option -g default-command \$SHELL
EOF

cat >> ${HOME}/.bashrc <<EOF
export PATH=${PATH}:${HOME}/maas/google_appengine
alias dev_appserver.py="dev_appserver.py --host 0.0.0.0 --admin_host 0.0.0.0"
alias appcfg.py="appcfg.py --oauth2 --noauth_local_webserver"
EOF

cat >> ${HOME}/.bash_logout <<EOF
rm -f \${HOME}/.appcfg_oauth2_tokens
EOF

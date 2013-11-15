#!/bin/bash
#set -x

trap 'exit' INT

USAGE="
  $0 operation [options]

  operations: 
    help - displays this text
    ssh instance - ssh into named instance
    setup [[start] end] - create instances
    teardown - delete instances
    list - list instances
    addimage - add codelab image
    delimage - delete codelab image
    addfirewall - add http firewall
    delfirewall - delete http firewall
"
DEBUG=yes
NUM_USERS=160
SCOPE="compute-rw,storage-full"
IMAGE=gs://codelab-machine-image/89f61a3e8ce6e3e6d13eb8b52ec35a15d47b063d.image.tar.gz
IMAGE_NAME=cosmos
PREFERRED_KERNEL=projects/google/global/kernels/gce-v20130603
HOME_IMAGE=https://www.googleapis.com/compute/v1beta16/projects/debian-cloud/global/images/debian-7-wheezy-v20131014
HOME_ZONE=us-central1-a
HOME_MACHINE_TYPE=n1-standard-1
STARTUP=script
GCUTIL="gcutil --credentials_file=~/.gcutil_auth_clsh"

START=1
END=$NUM_USERS

if [ "$1" = "help" ]
then
  echo -e "$USAGE"
  exit 0
elif [ "$1" = "" ]
then
  echo -e "$USAGE"
  exit 1
fi

OPER=$1
shift
if [ "$1" != "" ]
then
  START=$1
  END=$1
  shift
fi
if [ "$1" != "" ]
then
  END=$1
  shift
fi

echo running $OPER from $START to $END

function check {
  if [ $1 = 0 ]
  then
    echo $2
  else
    echo ERROR $2 
  fi
}

if [ "$DEBUG" = "yes" ]
then
  OUT=""
else
  OUT=" >/dev/null 2>&1"
fi

if [ "$OPER" = "ssh" ]
then
  NODE=gcecodelab$START
  HOMEDIR=/home/$NODE
  ADDR=`$GCUTIL --project=$NODE listinstances | grep " $NODE " | awk '{print $14}'`
  echo ssh $NODE@$ADDR
  ssh $NODE@$ADDR
elif [ "$OPER" = "addfirewall" ]
then
  for i in $(seq $START $END)
  do
    NODE=gcecodelab$i
    eval $GCUTIL --project=$NODE addfirewall gae --description=\"Incoming http allowed.\" --allowed=\"tcp:8080,tcp:8000\" $OUT
    check $? "opening firewall for node $NODE"
  done
elif [ "$OPER" = "delfirewall" ]
then
  for i in $(seq $START $END)
  do
    NODE=gcecodelab$i
    eval $GCUTIL --project=$NODE deletefirewall -f gae $OUT &
    #check $? "deleting firewall for node $NODE"
  done
  echo waiting for VMs to be added...
  wait
  echo done.
elif [ "$OPER" = "setup" ]
then
  for i in $(seq $START $END)
  do
    NODE=gcecodelab$i
    eval $GCUTIL --project=$NODE addinstance $NODE --zone=$HOME_ZONE --machine_type=$HOME_MACHINE_TYPE --metadata_from_file=startup-script:maas-startup.sh --service_account_scopes=$SCOPE --image=$HOME_IMAGE --persistent_boot_disk=false $OUT &
    #check $? "creating instance for node $NODE"
  done
  echo waiting for VMs to be added...
  wait
  echo done.
elif [ "$OPER" = "list" ]
then
    LINE="`printf "%-15.15s %-15.15s\n" "Node" "IP Address"`"
    echo "$LINE" >addrs
    echo "$LINE"
    for i in $(seq $START $END)
    do
      NODE=gcecodelab$i
      ADDR=`$GCUTIL --project=$NODE listinstances | grep " $NODE " | awk '{print $14}'`
      LINE="`printf "%-15.15s %-15.15s" $NODE $ADDR`"
      echo "$LINE" >>addrs
      echo "$LINE"
    done
elif [ "$OPER" = "teardown" ]
then
  for i in $(seq $START $END)
  do
    NODE=gcecodelab$i
    eval $GCUTIL --project=$NODE deleteinstance -f $NODE --zone=$HOME_ZONE $OUT &
  done
  echo waiting for VMs to be deleted...
  wait
  echo done.
elif [ "$OPER" = "addimage" ]
then
  for i in $(seq $START $END)
  do
    NODE=gcecodelab$i
    eval $GCUTIL --project=$NODE addimage $IMAGE_NAME $IMAGE \
      --preferred_kernel=$PREFERRED_KERNEL $OUT <<!
y
!
    check $? "adding image for node $NODE"
  done
elif [ "$OPER" = "delimage" ]
then
  for i in $(seq $START $END)
  do
    NODE=gcecodelab$i
    eval $GCUTIL --project=$NODE deleteimage -f $IMAGE_NAME $OUT 
    check $? "deleting image for node $NODE"
  done
else
  echo -e "$USAGE"
  exit 1
fi

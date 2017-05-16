from os import environ
from fabric.api import *
from fabric.context_managers import cd
from fabric.contrib.files import sed

# from ..keys import R_ROOT_PASS


"""
    Fabric file to upload public/private keys to remote servers
    and set up non-root users. Also prevents SSH-ing in with the
    root user.
"""

# run the bootstrap process as root before it is locked down
env.user = 'vagrant'

# the remote server's root password
# env.password = R_ROOT_PASS

# All IP addresses or hostnames of the servers you want to put
# your SSH keys and authorized_host  files on, ex: 192.168.1.1
env.hosts = ['127.0.0.1:2222']

# full name for the new non-root user
env.new_user_full_name = 'Your name'

# username for the new non-root user to be created
env.new_user = 'deployer'

# group name for the new non-root user to be created
env.new_user_grp = 'deployers'

# find running VM (assuming only one is running)
result = local('vagrant global-status | grep running', capture=True)
machineId = result.split()[0]

# use vagrant ssh key for the running VM
result = local('vagrant ssh-config {} | grep IdentityFile'.format(machineId), capture=True)

env.key_filename = result.split()[1]

# local filesystem directory where prod_key.pub and authorized_keys
# files are located (they will be scp'd to target host) don't include
# a trailing slash note: the tilde will resolve to your home directory
env.ssh_key_dir = '~/venv/towrec.com/towrec_project/ssh_keys'


"""
    The following functions should not be modified to
    complete the bootstrap process.
"""

def bootstrap():
    local('ssh-keygen -R %s' % env.host_string)
    sed('/etc/ssh/ssh_config', '^UsePAM yes', 'UsePAM no', use_sudo=True)
    sed('/etc/ssh/ssh_config', '^PermitRootLogin yes', 'PermitRootLogin no', use_sudo=True)
    sed('/etc/ssh/ssh_config', '^#PasswordAuthentication yes',
        'PasswordAuthentication no', use_sudo=True)
    # _create_privileged_group()
    # _create_privileged_user()
    _upload_keys(env.new_user)
    sudo('service ssh reload')


def _create_privileged_group():
    sudo('/usr/sbin/groupadd ' + env.new_user_grp)
    sudo('cp /etc/sudoers /etc/sudoers-backup')
    sudo('(cat /etc/sudoers-backup ; echo "%' + env.new_user_grp \
        + ' ALL=(ALL) ALL") > /etc/sudoers')
    sudo('chmod 440 /etc/sudoers')


def _create_privileged_user():
    sudo('/usr/sbin/useradd -c "%s" -m -g %s %s' % \
        (env.new_user_full_name, env.new_user_grp, env.new_user))
    sudo('/usr/bin/passwd %s' % env.new_user)
    sudo('/usr/sbin/usermod -a -G ' + env.new_user_grp + ' ' + \
        env.new_user)
    sudo('mkdir /home/%s/.ssh' % env.new_user)
    sudo('chown -R %s /home/%s/.ssh' % (env.new_user,
        env.new_user))
    sudo('chgrp -R %s /home/%s/.ssh' % (env.new_user_grp,
        env.new_user))


def _upload_keys(username):
    local('vagrant scp ' + env.ssh_key_dir + \
          '/prod_key.pub ' + env.ssh_key_dir + \
          '/authorized_keys ' + \
          username + '@' + env.host_string + ':~/.ssh')



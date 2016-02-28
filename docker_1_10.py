"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class docker_1_10(ShutItModule):


	def build(self, shutit):
		# Some useful API calls for reference. See shutit's docs for more info and options:
		#
		# ISSUING BASH COMMANDS
		# shutit.send(send,expect=<default>) - Send a command, wait for expect (string or compiled regexp)
		#                                      to be seen before continuing. By default this is managed
		#                                      by ShutIt with shell prompts.
		# shutit.multisend(send,send_dict)   - Send a command, dict contains {expect1:response1,expect2:response2,...}
		# shutit.send_and_get_output(send)   - Returns the output of the sent command
		# shutit.send_and_match_output(send, matches) 
		#                                    - Returns True if any lines in output match any of 
		#                                      the regexp strings in the matches list
		# shutit.send_until(send,regexps)    - Send command over and over until one of the regexps seen in the output.
		# shutit.run_script(script)          - Run the passed-in string as a script
		# shutit.install(package)            - Install a package
		# shutit.remove(package)             - Remove a package
		# shutit.login(user='root', command='su -')
		#                                    - Log user in with given command, and set up prompt and expects.
		#                                      Use this if your env (or more specifically, prompt) changes at all,
		#                                      eg reboot, bash, ssh
		# shutit.logout(command='exit')      - Clean up from a login.
		# 
		# COMMAND HELPER FUNCTIONS
		# shutit.add_to_bashrc(line)         - Add a line to bashrc
		# shutit.get_url(fname, locations)   - Get a file via url from locations specified in a list
		# shutit.get_ip_address()            - Returns the ip address of the target
		# shutit.command_available(command)  - Returns true if the command is available to run
		#
		# LOGGING AND DEBUG
		# shutit.log(msg,add_final_message=False) -
		#                                      Send a message to the log. add_final_message adds message to
		#                                      output at end of build
		# shutit.pause_point(msg='')         - Give control of the terminal to the user
		# shutit.step_through(msg='')        - Give control to the user and allow them to step through commands
		#
		# SENDING FILES/TEXT
		# shutit.send_file(path, contents)   - Send file to path on target with given contents as a string
		# shutit.send_host_file(path, hostfilepath)
		#                                    - Send file from host machine to path on the target
		# shutit.send_host_dir(path, hostfilepath)
		#                                    - Send directory and contents to path on the target
		# shutit.insert_text(text, fname, pattern)
		#                                    - Insert text into file fname after the first occurrence of 
		#                                      regexp pattern.
		# shutit.delete_text(text, fname, pattern)
		#                                    - Delete text from file fname after the first occurrence of
		#                                      regexp pattern.
		# shutit.replace_text(text, fname, pattern)
		#                                    - Replace text from file fname after the first occurrence of
		#                                      regexp pattern.
		# ENVIRONMENT QUERYING
		# shutit.host_file_exists(filename, directory=False)
		#                                    - Returns True if file exists on host
		# shutit.file_exists(filename, directory=False)
		#                                    - Returns True if file exists on target
		# shutit.user_exists(user)           - Returns True if the user exists on the target
		# shutit.package_installed(package)  - Returns True if the package exists on the target
		# shutit.set_password(password, user='')
		#                                    - Set password for a given user on target
		#
		# USER INTERACTION
		# shutit.get_input(msg,default,valid[],boolean?,ispass?)
		#                                    - Get input from user and return output
		# shutit.fail(msg)                   - Fail the program and exit with status 1
		# 
		shutit.send('rm -rf /tmp/docker1_10')
		box = shutit.send_and_get_output('vagrant box list 2>/dev/null | grep ubuntu/vivid64')
		if box == '':
			shutit.send('vagrant box add --provider virtualbox https://atlas.hashicorp.com/ubuntu/boxes/vivid64',note='Download the ubuntu vagrant box')
		shutit.send('mkdir /tmp/docker1_10 && cd /tmp/docker1_10 && vagrant init ubuntu/vivid64 && vagrant up',note='vagrant up')
		shutit.login(command='vagrant ssh',note='Log into the VM')
		shutit.login(user='root',command='sudo su - root')
		shutit.send('curl -sSL -O https://get.docker.com/builds/Linux/x86_64/docker-1.10.0 && chmod +x docker-1.10.0 && sudo mv docker-1.10.0 /usr/bin/docker')
		shutit.send('chmod +x /usr/bin/docker')
		#Runtime
		#Add --userns-remap flag to daemon to support user namespaces (previously in experimental) #19187
		shutit.send_file('/etc/subuid','dockremap:10000:1000',note='Create the subuid file for namespace support')
		shutit.send_file('/etc/subgid','dockremap:10000:1000',note='Create the subgid file for namespace support')
		shutit.send('nohup docker daemon --userns-remap=default &',note='Start the docker daemon with user namespace support')
		shutit.send('docker run -d --user=root --name sleeper busybox sleep 30',note='Run a container as root for thirty seconds')
		shutit.send('docker exec sleeper ps -a',note='Sleep is running as root in the container...')
		shutit.send('ps -ef | grep sleep',note='...but not as root on the host.')
		shutit.send('docker rm -f sleeper',note='Remove the sleeper container')
		#New docker update command that allows updating resource constraints on running containers #15078
		shutit.send_file('stresser.sh','''while /bin/true
do
	echo stressing
	stress --cpu 1 --timeout 100
	echo done stressing
	sleep 1
done''',note='Create the stresser script.')
		shutit.send_file('Dockerfile','''FROM debian
RUN apt-get update && apt-get install stress
ADD stresser.sh /stresser.sh
RUN chmod +x stresser.sh
CMD /bin/bash -c /stresser.sh''',note='Create the stresser image Dockerfile')
		shutit.send('docker build -t stress .',note='Build the stresser container')
		shutit.send('docker run -d --name stresser stress',note='Run up the stresser cotainer')
		shutit.send('sleep 2 && top -b | head',note='CPU is stressed!')
		shutit.send('docker update --cpu-period 50000 --cpu-quota 25000 stresser',note='Dynamically limit the CPU of the running container to half a CPU')
		shutit.send('sleep 2 && top -b | head',note='CPU is less stressed')
		shutit.send('docker rm -f stresser')
		#Updated docker events to include more meta-data and event types #18888
		shutit.send('docker events --since 0 --until 1',note='More useful output in docker events.')
		#Show the number of running, stopped, and paused containers in docker info #19249 #Show the OSType and Architecture in docker info #17478
		shutit.send('docker info',note='More useful information in docker info')

		#Add --tmpfs flag to docker run to create a tmpfs mount in a container #13587
		shutit.send("""docker run --tmpfs /mytmpfs debian bash -c 'mount | grep mytmpfs'""",note='Create an in-memory filesystem with --tmpfs')

		#Networking
		#Add --internal flag to network create to restrict external access to and from the network #19276
		shutit.send('docker network create --internal mynet',note='Create an internal docker network')
		shutit.send('docker network ls',note='list our available networks')
		shutit.send('docker run -d --name sleeper debian sleep infinity',note='Create a container')
		shutit.send('docker exec -ti sleeper ping -W 1 -c 3 google.com',note='It can ping the outside world.')
		shutit.send('docker network disconnect bridge sleeper',note='Disconnect the default open network bridge.')
		shutit.send('docker network connect mynet sleeper',note='Connect our internal network bridge')
		shutit.send('docker exec -ti sleeper ping -W 1 -c 3 google.com',note='We can no longer access the outside world from this network.')

		#Add default seccomp profile #18780
		#Add support for custom seccomp profiles in --security-opt #17989
		shutit.send_file('/seccomp.json','''{
    "defaultAction": "SCMP_ACT_ALLOW",
    "syscalls": [
        {
            "name": "mkdir",
            "action": "SCMP_ACT_ERRNO"
        }
    ]
}''',note='Set up a seccomp file that disallows the ability to make a directory')
		shutit.login(command='docker run -it --security-opt seccomp:/seccomp.json debian',note='Log into a docker with a seccomp profile set')
		shutit.send('whoami',note='I am root')
		shutit.send('cd $HOME',note='I am in my home directory')
		shutit.send('touch afile',note='I can create a file')
		shutit.send('mkdir adir',note='But I cannot create a directory!',check_exit=False)
		shutit.logout()
#TODO
		#Security
		#Add --authorization-plugin flag to daemon to customize ACLs #15365


		shutit.logout()
		return True

	def get_config(self, shutit):
		# CONFIGURATION
		# shutit.get_config(module_id,option,default=None,boolean=False)
		#                                    - Get configuration value, boolean indicates whether the item is 
		#                                      a boolean type, eg get the config with:
		# shutit.get_config(self.module_id, 'myconfig', default='a value')
		#                                      and reference in your code with:
		# shutit.cfg[self.module_id]['myconfig']
		return True

	def test(self, shutit):
		# For test cycle part of the ShutIt build.
		return True

	def finalize(self, shutit):
		# Any cleanup required at the end.
		return True
	
	def is_installed(self, shutit):
		return False


def module():
	return docker_1_10(
		'shutit.docker_1.9.docker_1_10.docker_1_10', 1113159394.00,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['tk.shutit.vagrant.vagrant.vagrant']
	)


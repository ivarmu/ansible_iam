# ansible

Callback Plugins
================

    callback: counter_enabled
    type: stdout
    short_description: adds counters to the output items (tasks and hosts/task)
    description:
      - Use this callback when you need a kind of progress bar on a large environments
      - You will know how many tasks has the playbook to run, and wich one is actually running
      - You will know how many hosts may run a task, and wich of them is actually running
    version_added: "2.5.2"
    extends_documentation_fragment:
      - default_callback
    requirements:
      - set as stdout callback in ansible.cfg: stdout_callback = counter_enabled

Output example for simple playbook:

```
ansible-playbook -i hosts test.yml

TASK 1/4 [Debug] ***************************************************************************************************************************************************************
ok: 1/2 [iamlab.iam.lab -> localhost] => {
    "HOST_COUNT": "2"
}
ok: 2/2 [localhost -> localhost] => {
    "HOST_COUNT": "2"
}

TASK 2/4 [Test task 1] *********************************************************************************************************************************************************
changed: 1/2 [localhost]
changed: 2/2 [iamlab.iam.lab]

TASK 3/4 [Test task 2] *********************************************************************************************************************************************************
changed: 1/2 [localhost]
changed: 2/2 [iamlab.iam.lab]

TASK 4/4 [Test task 3] *********************************************************************************************************************************************************
fatal: 1/2 [iamlab.iam.lab]: FAILED! => {"changed": true, "cmd": "ls -d /", "delta": "0:00:00.003744", "end": "2018-05-17 13:11:48.828840", "failed_when_result": true, "rc": 0, "start": "2018-05-17 13:11:48.825096", "stderr": "", "stderr_lines": [], "stdout": "/", "stdout_lines": ["/"]}
fatal: 2/2 [localhost]: FAILED! => {"changed": true, "cmd": "ls -d /", "delta": "0:00:00.003260", "end": "2018-05-17 13:11:48.835607", "failed_when_result": true, "rc": 0, "start": "2018-05-17 13:11:48.832347", "stderr": "", "stderr_lines": [], "stdout": "/", "stdout_lines": ["/"]}
	to retry, use: --limit @/home/ivan/ansible/test/iam/test.retry

```

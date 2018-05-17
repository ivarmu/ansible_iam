# (c) 2018, Ivan Aragones Muniesa <ivan.aragones.muniesa@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
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
'''


from ansible import constants as C
from ansible.plugins.callback import CallbackBase
from ansible.utils.color import colorize, hostcolor
from ansible.template import Templar
from ansible.plugins.strategy import SharedPluginLoaderObj
from ansible.playbook.task_include import TaskInclude

class CallbackModule(CallbackBase):

    '''
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'counter_enabled'

    _task_counter = 1
    _task_total = 0
    _host_counter = 1
    _host_total = 0

    def _all_vars(self, host=None, task=None):
        # host and task need to be specified in case 'magic variables' (host vars, group vars, etc) need to be loaded as well
        return self._play.get_variable_manager().get_vars(
            play=self._play,
            host=host,
            task=task
        )

    def v2_playbook_on_start(self, playbook):
        self._playbook = playbook

    def v2_playbook_on_play_start(self, play):
        self._play = play
        name = play.get_name().strip()
        if not name:
            msg = "PLAY"
        else:
            msg = "PLAY [%s]" % name

        #self._display.banner(msg)
        self._host_total=len(self._all_vars()['vars']['ansible_play_hosts_all'])
        self._task_total=len(self._play.get_tasks()[0])

    def v2_playbook_on_task_start(self, task, is_conditional):
        args = ''
        # args can be specified as no_log in several places: in the task or in
        # the argument spec.  We can check whether the task is no_log but the
        # argument spec can't be because that is only run on the target
        # machine and we haven't run it thereyet at this time.
        #
        # So we give people a config option to affect display of the args so
        # that they can secure this if they feel that their stdout is insecure
        # (shoulder surfing, logging stdout straight to a file, etc).
        if not task.no_log and C.DISPLAY_ARGS_TO_STDOUT:
            args = ', '.join(('%s=%s' % a for a in task.args.items()))
            args = ' %s' % args
        self._display.banner("TASK %d/%d [%s%s]" % (self._task_counter, self._task_total, task.get_name().strip(), args))
        if self._display.verbosity >= 2:
            path = task.get_path()
            if path:
                self._display.display("task path: %s" % path, color=C.COLOR_DEBUG)
        self._host_counter = 0
        self._task_counter += 1

    def v2_runner_on_ok(self, result):

        self._host_counter += 1

        delegated_vars = result._result.get('_ansible_delegated_vars', None)

        if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
            self._print_task_banner(result._task)

        if isinstance(result._task, TaskInclude):
            return
        elif result._result.get('changed', False):
            if delegated_vars:
                msg = "changed: %d/%d [%s -> %s]" % (self._host_counter, self._host_total, result._host.get_name(), delegated_vars['ansible_host'])
            else:
                msg = "changed: %d/%d [%s]" % (self._host_counter, self._host_total, result._host.get_name())
            color = C.COLOR_CHANGED
        else:
            if delegated_vars:
                msg = "ok: %d/%d [%s -> %s]" % (self._host_counter, self._host_total, result._host.get_name(), delegated_vars['ansible_host'])
            else:
                msg = "ok: %d/%d [%s]" % (self._host_counter, self._host_total, result._host.get_name())
            color = C.COLOR_OK

        self._handle_warnings(result._result)

        if result._task.loop and 'results' in result._result:
            self._process_items(result)
        else:
            self._clean_results(result._result, result._task.action)

            if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and '_ansible_verbose_override' not in result._result:
                msg += " => %s" % (self._dump_results(result._result),)
            self._display.display(msg, color=color)

    def v2_runner_on_failed(self, result, ignore_errors=False):

        self._host_counter += 1

        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        self._clean_results(result._result, result._task.action)

        if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
            self._print_task_banner(result._task)

        self._handle_exception(result._result)
        self._handle_warnings(result._result)

        if result._task.loop and 'results' in result._result:
            self._process_items(result)

        else:
            if delegated_vars:
                self._display.display("fatal: %d/%d [%s -> %s]: FAILED! => %s" % (self._host_counter, self._host_total, 
                                                                            result._host.get_name(), delegated_vars['ansible_host'],
                                                                            self._dump_results(result._result)), color=C.COLOR_ERROR)
            else:
                self._display.display("fatal: %d/%d [%s]: FAILED! => %s" % (self._host_counter, self._host_total, 
                                                                            result._host.get_name(), self._dump_results(result._result)),
                                                                            color=C.COLOR_ERROR)

        if ignore_errors:
            self._display.display("...ignoring", color=C.COLOR_SKIP)

    def v2_runner_on_skipped(self, result):
        self._host_counter += 1

        if self._plugin_options.get('show_skipped_hosts', C.DISPLAY_SKIPPED_HOSTS):  # fallback on constants for inherited plugins missing docs

            self._clean_results(result._result, result._task.action)

            if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
                self._print_task_banner(result._task)

            if result._task.loop and 'results' in result._result:
                self._process_items(result)
            else:
                msg = "skipping: %d/%d [%s]" % (self._host_counter, self._host_total, result._host.get_name())
                if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and '_ansible_verbose_override' not in result._result:
                    msg += " => %s" % self._dump_results(result._result)
                self._display.display(msg, color=C.COLOR_SKIP)

    def v2_runner_on_unreachable(self, result):
        self._host_counter += 1

        if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
            self._print_task_banner(result._task)

        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        if delegated_vars:
            self._display.display("fatal: %d/%d [%s -> %s]: UNREACHABLE! => %s" % (self._host_counter, self._host_total, 
                                                                             result._host.get_name(), delegated_vars['ansible_host'],
                                                                             self._dump_results(result._result)),
                                  color=C.COLOR_UNREACHABLE)
        else:
            self._display.display("fatal: %d/%d [%s]: UNREACHABLE! => %s" % (self._host_counter, self._host_total, 
                                                                             result._host.get_name(), self._dump_results(result._result)),
                                                                             color=C.COLOR_UNREACHABLE)

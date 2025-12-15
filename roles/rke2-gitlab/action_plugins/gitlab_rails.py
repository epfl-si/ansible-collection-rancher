from functools import cached_property
import json
import yaml
import shlex

from kubernetes.client.apis import core_v1_api
from kubernetes.stream import stream

from ansible.plugins.action import ActionBase
from ansible_collections.epfl_si.actions.plugins.module_utils.ansible_api import AnsibleActions, AnsibleResults

from ansible_collections.epfl_si.k8s.plugins.module_utils.kubeconfig import Kubeconfig

class GitlabRailsAction (ActionBase):
    """Action class for postconditions expressed as Ruby code, to be run in the Rails console.

    Given that running the Rails console is expensive, we want to
    amortize any number of Rails postcondition classes into one
    `epfl_si.k8s.k8s_exec` task. This also means that inheriting from
    Postcondition is not a good fit (we don't want two round-trips for
    `holds` and `enforce`); which in turn, forces this class to
    implement `--check` on its own.
    """
    @AnsibleActions.run_method
    def run (self, args, ansible_api):
        self.ansible_api = ansible_api
        self.client = Kubeconfig(
            args=args,
            vars=ansible_api.jinja.vars,
            expand_vars_fn=ansible_api.jinja.expand).get_api_client()

        self.ruby_postconditions_class_text = args["ruby_postconditions_class"]
        self.namespace = args["namespace"]

        return self._execute_in_rails_console(self._aggregated_ruby_code())

    @property
    def _is_check_mode (self):
        return self.ansible_api.check_mode.is_active

    def _aggregated_ruby_code (self):
        # Debugging tip: put prologue, snippet and epilogue in a
        # `/tmp/test.rb` file in the `gitlab-webservice-default-xxx-yyy`
        # container of the `gitlab-test` namespace; [run the Rails
        # console](https://gitlab.com/epfl-isasfsd/gitlab-ops/-/wikis/RunbookConsoleRails) and type
        #
        #    load "/tmp/test.rb"
        #
        # at the prompt
        return """
import 'json'
import 'set'

class ActiveRecordSpy
  attr_reader :touched

  def initialize
    @touched = Set.new
    @changed_before = Set.new
  end

  def changed?(record)
    record.new_record? || record.changed? || @changed_before.include?(record)
  end

  def mark_if_changed(record)
    @changed_before << record if record.new_record? || record.changed?
  end

  def track(record)
    @touched << record
  end

  def self.capture
    spy = new

    begin
      init_cbs_orig = []
      save_cbs_orig = []
      ActiveRecord::Base._initialize_callbacks.each { |cb| init_cbs_orig << cb }
      ActiveRecord::Base._save_callbacks.each { |cb| save_cbs_orig << cb }

      ActiveRecord::Base.after_initialize do |record|
        spy.track(record)
      end

      ActiveRecord::Base.before_save do |record|
        spy.mark_if_changed(record)
      end

      yield

    ensure
      ActiveRecord::Base._initialize_callbacks.clear
      ActiveRecord::Base._initialize_callbacks.append(*init_cbs_orig)
      ActiveRecord::Base._save_callbacks.clear
      ActiveRecord::Base._save_callbacks.append(*save_cbs_orig)
    end

    spy
  end
end

class Postconditions
  Postcondition = Struct.new(:name, :block)

  def self.postconditions
    @postconditions ||= {}
  end

  def self.postcondition(name, &block)
    postconditions[name] = Postcondition.new(name, block)
  end

  def run_postconditions! (check: false)
    ansible_response = {}

    ActiveRecord::Base.transaction do
      self.class.postconditions.values.each do |pc|
        begin
          spy = ActiveRecordSpy.capture do
            instance_exec(&pc.block)
          end

          spy.touched.each do |record|
            if spy.changed?(record)
              (ansible_response["changed"] ||= {})[pc.name] = true
              record.save!
            end
          end
        rescue => exception
          ansible_response["failed"] = true
          (ansible_response["message"] ||= {})[pc.name] = [
            exception.to_s,
            *exception.backtrace
          ]
        end
      end
      raise ActiveRecord::Rollback if check
    end

    ansible_response
  end
end

""" + self.ruby_postconditions_class_text + """

p = Postconditions.descendants[0].new
puts JSON.pretty_generate(p.run_postconditions!(check: %s))

""" % ("true" if self._is_check_mode else "false")

    def _execute_in_rails_console (self, ruby_text):
        api = core_v1_api.CoreV1Api(self.client.client)

        # SIGHH. https://github.com/kubernetes-client/python/issues/2371
        end_of_ruby_code = "##### END OF RUBY CODE #####"

        resp = stream(
            api.connect_get_namespaced_pod_exec,
            self._pod_name,
            self.namespace,
            container="webservice",
            stdin=True,
            stdout=True,
            stderr=True,
            tty=False,
            _preload_content=False,
            command=[
                "/bin/bash", "-c",
                "sed '/%s/q' | /srv/gitlab/bin/rails runner -" %
                end_of_ruby_code])

        resp.write_stdin("%s\n\n%s\n" %(ruby_text, end_of_ruby_code))
        stdout, stderr = [], []
        while resp.is_open():
            resp.update(timeout=1)
            if resp.peek_stdout():
                stdout.append(resp.read_stdout())
            if resp.peek_stderr():
                stderr.append(resp.read_stderr())

        stdout="".join(stdout)
        stderr="".join(stderr)

        status = yaml.safe_load(resp.read_channel(3))
        if status["status"] == "Success":
            rc = 0
        else:
            rc = int(status["details"]["causes"][0]["message"])

        error_result = dict(
            changed=True,
            failed=True,
            stdout=stdout,
            stderr=stderr,
            rc=rc,
            return_code=rc)

        if rc == 0:
            try:
                return json.loads(stdout)
            except Exception as e:
                error_result["message"] = str(e)

        return error_result

    @cached_property
    def _pod_name (self):
        for pod in self.ansible_api.jinja.lookup(
            "epfl_si.k8s.k8s",
            namespace=self.namespace,
            kind="Pod"):

            if pod["metadata"].get("labels").get("app") == "webservice":
                return pod["metadata"]["name"]

ActionModule = GitlabRailsAction

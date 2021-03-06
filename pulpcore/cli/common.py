import click
import datetime
import json
import pkg_resources
import time

from pulpcore.cli.openapi import OpenAPI


class PulpJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            super(json.JSONEncoder).default(obj)


class PulpContext:
    def output_result(self, result):
        if self.format == "json":
            click.echo(json.dumps(result, cls=PulpJSONEncoder, indent=2))

    def call(self, operation_id, *args, **kwargs):
        result = self.api.call(operation_id, *args, **kwargs)
        if "task" in result:
            task_href = result["task"]
            click.echo(f"Started task {task_href}")
            result = self.wait_for_task(task_href)
            click.echo("Done.")
        return result

    def wait_for_task(self, task_href, timeout=120):
        while timeout:
            timeout -= 1
            task = self.api.call("tasks_read", parameters={"task_href": task_href})
            if task["state"] == "completed":
                return task
            if task["state"] == "failed":
                raise Exception("Task failed")
            time.sleep(1)
            timeout -= 1
            click.echo(".", nl=False)
        raise Exception("Task timed out")


@click.group()
@click.version_option(prog_name="pulp3 command line interface")
@click.option("--base-url", default="http://localhost", help="Api base url")
@click.option("--user", default="admin", help="Username on pulp server")
# @click.option("--password", prompt=True, hide_input=True, help="Password on pulp server")
@click.option("--password", default="password", help="Password on pulp server")
@click.option("--verify-ssl", is_flag=True, default=True, help="Verify SSL connection")
@click.option("--format", type=click.Choice(["json"], case_sensitive=False), default="json")
@click.pass_context
def main(ctx, base_url, user, password, verify_ssl, format):
    ctx.ensure_object(PulpContext)
    ctx.obj.api = OpenAPI(base_url=base_url, doc_path="/pulp/api/v3/docs/api.json", username=user, password=password, validate_certs=verify_ssl, refresh_cache=True)
    ctx.obj.format = format

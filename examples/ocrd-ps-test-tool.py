#!/usr/bin/python
import click
import sh
from pathlib import Path
import json
import time
import re
import sys
import yaml

EXAMPLE_WF = f"{Path().absolute()}/wf_server_example.nf"
assert Path("config.yaml").exists(), "config.yaml required. Use config.example.yaml as template"
config_dict = yaml.safe_load(open("config.yaml"))
globals().update(config_dict)


@click.group()
@click.option("--local", is_flag=True, default=False, help=f"run the command on {HOST_LOCAL}")
def cli(local):
    """ Test the processing server
    """
    # host for workspaces and workflows
    global host_global
    # host for processing-servers (is the same as host_global on vm)
    global host_ps_global
    if local:
        host_global = HOST_LOCAL
        host_ps_global = HOST_PS_LOCAL
    else:
        host_global = HOST
        host_ps_global = HOST


@click.group("proc")
def processor_cli():
    """Run single processors
    """
    pass


@processor_cli.command("dummy")
def processor_dummy():
    """ocrd-dummy

    Upload a workspace (put), run ocrd-dummy, download the workspace, ensure new filegroup
    """
    run_processor("ocrd-dummy", "OCR-D-IMG", "OCR-D-DUMMY")


@processor_cli.command("cis-binarize")
def cis_binarize():
    """ocrd-cis-ocropy-binarize

    Upload a workspace (put), run ocrd-cis-ocropy-binarize, download the workspace, ensure new
    filegroup exsits
    """
    run_processor("ocrd-cis-ocropy-binarize", "OCR-D-IMG", "OCR-D-BIN")


@processor_cli.command("cis-segment")
def cis_segment():
    """ocrd-cis-ocropy-segment

    Upload a workspace (put), run ocrd-cis-ocropy-binarize, download the workspace, ensure new
    filegroup exsits, then run ocrd-cis-ocropy-segment with the output-filegrp of binarize and
    ensure it succeeded
    """
    bin_filegrp = "OCR-D-BIN"
    output_filegrp = "OCR-D-SEG"

    upload_workspace()

    # cis-segment demands a binarized image
    job_id = execute_processor(
        "ocrd-cis-ocropy-binarize",
        "OCR-D-IMG",
        bin_filegrp,
    )

    wait_for_job(job_id)

    verify_filegrp_exists(bin_filegrp)

    job_id = execute_processor(
        "ocrd-cis-ocropy-segment",
        bin_filegrp,
        output_filegrp,
        parameters={"level-of-operation": "page"}
    )

    wait_for_job(job_id, timeout=30)

    verify_filegrp_exists(output_filegrp)


@processor_cli.command("cis-dewarp")
def cis_dewarp():
    """ocrd-cis-ocropy-dewarp
    """
    run_processor("ocrd-cis-ocropy-dewarp", "OCR-D-IMG", "OCR-D-SEG-LINE")


@processor_cli.command("anybase-crop")
def anybase_crop():
    """ocrd-anybaseocr-crop
    """
    run_processor("ocrd-anybaseocr-crop", "OCR-D-IMG", "OCR-D-IMG-CROP")


@processor_cli.command("skimage-bin")
def skimage_bin():
    """ocrd-skimage-binarize
    """
    run_processor("ocrd-skimage-binarize", "OCR-D-IMG", "OCR-D-DENOISE",
                  {"method": "li"})


@processor_cli.command("skimage-denoise")
def skimage_denoise():
    """ocrd-skimage-denoise
    """
    run_processor("ocrd-skimage-denoise", "OCR-D-IMG", "OCR-D-DENOISE-DESKEW",
                  {"level-of-operation": "page"})


@processor_cli.command("tesserocr-deskew")
def tesserocr_deskew():
    """ocrd-tesserocr-deskew
    """
    run_processor("ocrd-tesserocr-deskew", "OCR-D-IMG", "OCR-D-BIN-DENOISE-DESKEW",
                  {"operation_level": "page"})


@processor_cli.command("calamari-rec")
def calamari_recognize():
    """ocrd-calamari-recognize
    """
    upload_workspace(DEFAULT_WORKSPACE_ID)
    run_processor("ocrd-calamari-recognize", "OCR-D-IMG", "OCR-D-OCR",
                  {"checkpoint_dir": "qurator-gt4histocr-1.0"}, timeout=45)


@processor_cli.command("olena-bin")
def olena_binarize():
    """ocrd-olena-binarize
    """
    upload_workspace(DEFAULT_WORKSPACE_ID)
    run_processor("ocrd-olena-binarize", "OCR-D-IMG", "OCR-D-BINPAGE",
                  {"impl": "sauvola-ms-split", "dpi": 300}, timeout=60)


@processor_cli.command("segment-repair")
def segment_repair():
    """ocrd-segment-repair
    """
    upload_workspace(DEFAULT_WORKSPACE_ID)
    run_processor("ocrd-segment-repair", "OCR-D-IMG", "OCR-D-SEGMENT-REPAIR",
                  {"plausibilize": True, "plausibilize_merge_min_overlap": 0.7}, timeout=60)


@cli.command()
def multiproc():
    """Test multiple single processors in succession

    Upload a workspace (put), run multiple processors which depend on the output of each other
    """
    upload_workspace()

    run_processor("ocrd-cis-ocropy-binarize", "OCR-D-IMG", "OCR-D-BIN")
    run_processor("ocrd-anybaseocr-crop", "OCR-D-BIN", "OCR-D-CROP")
    run_processor("ocrd-skimage-binarize", "OCR-D-CROP", "OCR-D-BIN2",
                  parameters={"method": "li"})
    run_processor("ocrd-skimage-denoise", "OCR-D-BIN2", "OCR-D-BIN-DENOISE",
                  parameters={"level-of-operation": "page"})
    run_processor("ocrd-tesserocr-deskew", "OCR-D-BIN-DENOISE", "OCR-D-BIN-DENOISE-DESKE",
                  parameters={"operation_level": "page"})
    run_processor("ocrd-cis-ocropy-segment", "OCR-D-BIN-DENOISE-DESKE", "OCR-D-SEG",
                  parameters={"level-of-operation": "page"})
    run_processor("ocrd-cis-ocropy-dewarp", "OCR-D-SEG", "OCR-D-SEG-LINE-RESEG-DEWARP")
    run_processor("ocrd-calamari-recognize", "OCR-D-SEG-LINE-RESEG-DEWARP", "OCR-D-OCR",
                  parameters={"checkpoint_dir": "qurator-gt4histocr-1.0"})


@cli.command()
def multiproc2():
    """Test multiple single processors in succession

    This one runs ocrd-tesserocr-recognize and then ocrd-fileformat-transform
    """
    upload_workspace()

    run_processor("ocrd-tesserocr-recognize", "OCR-D-IMG", "OCR-D-OCR",
                  parameters={"model": "frak2021"})
    run_processor(
        "ocrd-fileformat-transform", "OCR-D-OCR", "FULLTEXT",
        parameters={
            "from-to": "page alto",
            "script-args": "--no-check-border --dummy-word"
        },
        timeout=45
    )


@cli.command()
def simple_workflow():
    """ Test the one-processor-workflow with ocrd-dummy

    Upload a workflow (put) and a workspace, execute it, download it an ensure filegrp created
    """
    upload_workspace()
    workflow_id = "test1-w"

    print("uploading(PUT) a workflow")
    output = sh.curl(
        "-X", "PUT",
        f"http://{host_global}/workflow/{workflow_id}",
        "-H", "content-type: multipart/form-data",
        "-F", f"nextflow_script=@{EXAMPLE_WF_SIMPLE}",
        "--user", f"{USER}:{PASSWORD}",
    )

    body = {
        "workspace_id": DEFAULT_WORKSPACE_ID
    }

    print("triggering a workflow run")
    output = sh.curl(
        "-X", "POST",
        "-H", "Content-Type: application/json",
        f"http://{host_global}/workflow/{workflow_id}",
        "-d", json.dumps(body),
        "--user", f"{USER}:{PASSWORD}",
    )
    res = json.loads(output)
    job_id = res['resource_id']

    print("starting to wait for workflow job to finish")
    wait_for_workflow_job(workflow_id, job_id, timeout=15)
    verify_filegrp_exists("OCR-D-DUMMY")


@cli.command()
@click.argument("workflow", required=False, default=EXAMPLE_WF)
@click.option("final_filegrp", "-e", "--expected", help="FileGRP to verify in result-ocrd-zip",
              default="OCR-D-OCR")
def run_workflow(workflow, final_filegrp):
    """ Run wf_server_example.nf script

    Upload the workflow (put) and the default workspace, execute it, wait until finished, download
    it an ensure filegroup exists

    https://github.com/MehmedGIT/wf_server_nf_script/blob/master/wf_server_example.nf
    """
    if not Path(workflow).exists():
        print(f"provided workflow '{workflow}' not found")
        exit(1)

    upload_workspace()
    workflow_id = "test1-w"

    print("uploading(PUT) a workflow")
    output = sh.curl(
        "-X", "PUT",
        f"http://{host_global}/workflow/{workflow_id}",
        "-H", "content-type: multipart/form-data",
        "-F", f"nextflow_script=@{workflow}",
        "--user", f"{USER}:{PASSWORD}",
    )

    body = {
        "workspace_id": DEFAULT_WORKSPACE_ID
    }

    print("triggering a workflow run")
    output = sh.curl(
        "-X", "POST",
        "-H", "Content-Type: application/json",
        f"http://{host_global}/workflow/{workflow_id}",
        "-d", json.dumps(body),
        "--user", f"{USER}:{PASSWORD}",
    )
    res = json.loads(output)
    job_id = res['resource_id']

    wait_for_workflow_job(workflow_id, job_id, timeout=240)
    verify_filegrp_exists(final_filegrp)


@cli.command()
def upload():
    """Upload default workspaces

    Upload a workspace (put), ensure it can be downloaded
    """
    upload_workspace()
    verify_filegrp_exists("OCR-D-IMG")


@cli.command()
def download():
    """Download default workspaces and save as foo.zip

    """
    verify_filegrp_exists("OCR-D-IMG")


@cli.command()
def list_processors():
    """List available processors of server
    """
    output = sh.curl(
        f"http://{host_global}/processor",
        "-H", "accept: application/json"
    )
    print(output)


@cli.command()
@click.argument("processor_name")
def get_tool(processor_name):
    """Get ocrd-tool of processor
    """
    output = sh.curl(
        f"http://{host_global}/processor/{processor_name}",
        "-H", "accept: application/json"
    )
    sh.jq("--indent", "4", _in=output, _out=sys.stdout)


def run_processor(name, input_filegrp, output_filegrp, parameters={},
                  workspace_id=DEFAULT_WORKSPACE_ID, timeout=15):
    job_id = execute_processor(
        name,
        input_filegrp,
        output_filegrp,
        parameters=parameters
    )
    wait_for_job(job_id, timeout=timeout)
    verify_filegrp_exists(output_filegrp)


def verify_filegrp_exists(filegrp, workspace_id=DEFAULT_WORKSPACE_ID):
    print(f"downloading workspace '{workspace_id}' and verifying file-grp {filegrp} exists")
    sh.curl(
        f"http://{host_global}/workspace/{workspace_id}",
        "-H", "accept: application/vnd.ocrd+zip",
        "-o", "foo.zip"
    )

    output = sh.unzip("-l", "foo.zip")
    regex = r"[\s]+data/" + f"{filegrp}" + r"/$"
    x = re.search(regex, output, re.M)
    if not x:
        print(f"FAIL: expected file-grp '{filegrp}' not found in workspace: '{workspace_id}'. "
              f"Unzip output:\n{output}")
    else:
        print(f"success: found file-grp '{filegrp}' in workspace: '{workspace_id}'")


def upload_workspace(workspace_id=DEFAULT_WORKSPACE_ID):
    """upload the example workspace with curl and verify `resource_id` is returned
    """
    print("uploading(PUT) a workspace")
    output = sh.curl(
        "-X", "PUT",
        f"http://{host_global}/workspace/{workspace_id}",
        "-H", "content-type: multipart/form-data",
        "-F", f"workspace=@{EXAMPLE_WS}",
        "--user", f"{USER}:{PASSWORD}",
    )
    res = json.loads(output)
    if "resource_id" not in res:
        print("error uploading workspace")
        exit(1)


def wait_for_job(job_id, timeout=15):
    """query for `job_id` with curl until error or success
    """

    print(f"starting to wait for job {job_id}")
    counter = timeout
    while counter > 0:
        output = sh.curl(
            f"http://{host_ps_global}/processor/ocrd-dummy/{job_id}",
        )
        res = json.loads(output)
        if 'state' not in res:
            print(f"trying to read state for job '{job_id}'. Expecting json containing 'state'' but"
                  f" got:\n{output}")
            exit(1)
        status = res['state']
        if status == "SUCCESS":
            break
        elif status == "FAILED":
            raise Exception(f"job {job_id} failed. Status is {status}")
        else:
            counter -= 1
            time.sleep(1)
    else:
        print("job didn't finish in time")
        raise Exception("Job didn't finish in time")
    print(f"successfully finished waiting for job {job_id}")


def wait_for_workflow_job(workflow_id, job_id, timeout=60):
    """ query for `workflow_id` and `job_id` with curl until finished
    """
    print("starting to wait for workflow job to finish")
    counter = timeout
    while counter > 0:
        output = sh.curl(
            f"http://{host_global}/workflow/{workflow_id}/{job_id}",
        )
        try:
            res = json.loads(output)
        except Exception:
            print("wait_for_workflow_job: cannot parse following response as json:")
            print(output)
            exit(0)
        status = res['job_state']
        if counter % 5 == 0:
            print(status)
        if status == "STOPPED":
            break
        else:
            counter -= 1
            time.sleep(1)
    else:
        print("workflow job didn't finish in time")
        raise Exception("workflow job didn't finish in time")
    print(f"job: '{job_id}' of workflow: '{workflow_id}' finished")


def execute_processor(processor_name, input_filegrp, output_filegrp, parameters={},
                      workspace_id=DEFAULT_WORKSPACE_ID):
    body = {
        "workspace_id": workspace_id,
        "input_file_grps": [input_filegrp],
        "output_file_grps": [output_filegrp],
        "parameters": parameters,
    }

    print(f"executing {processor_name} on {host_ps_global}")
    output = sh.curl(
        "-X", "POST",
        f"http://{host_ps_global}/processor/{processor_name}",
        "-H", "accept: application/json",
        "-H", "content-type: application/json",
        "-d", json.dumps(body),
    )

    try:
        res = json.loads(output)
    except Exception:
        print("error parsing json in 'execute_processor'. Output was:")
        print(output)
        exit(1)

    if 'job_id' in res:
        return res['job_id']
    else:
        print(f"error trying to execute {processor_name} on '{host_ps_global}'. "
              f"curl output: \n{res}")
        exit(1)


cli.add_command(processor_cli)

if __name__ == "__main__":
    cli()

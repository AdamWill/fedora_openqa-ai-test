Fedora openQA scheduler and report tools
========================================

This repository contains a Python library (`fedora_openqa`) and CLI tool (`fedora-openqa`) that handle scheduling jobs in Fedora's instances ([production](https://openqa.fedoraproject.org) and [staging](https://openqa.stg.fedoraproject.org)) of [openQA](http://open.qa/). The library contains several fedmsg consumers which together form a fully automated pipeline for running tests in Fedora's official openQA instances. Jobs are scheduled in response to fedmsgs from release engineering. When a job completes, a fedmsg is emitted, and the 'reporter' consumers forward results to [Wikitcms](https://fedoraproject.org/wiki/Wikitcms) and [ResultsDB](https://fedoraproject.org/wiki/ResultsDB). The CLI allows manual triggering of jobs and reporting of results for testing with a local openQA deployment, or in case some issue in the automated pipeline requires manual intervention.

This repository does not contain the actual Fedora openQA tests. Those can be found [here](https://pagure.io/fedora-qa/os-autoinst-distri-fedora).

For general information on openQA in Fedora, including an overview of the system and how to install your own instance for testing, please see [the Fedora openQA wiki page](https://fedoraproject.org/wiki/openQA).

Issues
------

[Issues](https://pagure.io/fedora-qa/fedora_openqa/issues) and [pull requests](https://pagure.io/fedora-qa/fedora_openqa/pull-requests) are tracked in [fedora_openqa Pagure](https://pagure.io/fedora-qa/fedora_openqa). Pagure uses a Github-like pull request workflow, so if you're familiar with that, you can easily submit Pagure pull requests. If not, you can read up in the [Pagure documentation](https://docs.pagure.org/pagure/usage/index.html).

Note that this repository does not use the 'gitflow' system, so the main development branch is `master`: please branch from `master` and submit diffs against it. Running the unit tests is not yet integrated into the diff process, so you do not have to follow the instructions regarding `virtualenv`, but please do run the tests manually to check any diffs you submit if possible.

Requirements
------------

**NOTE**: If you have deployed openQA in docker containers, note that this tool should be configured and run (and installed, if desired) on the **host**, not in any of the containers.

To use the `fedora-openqa` CLI, you do not have to do a system install, you can run it directly from the source tree. However, you do need to ensure some dependencies are available. Most of them are available as packages on Fedora, and can be installed as follows:

    dnf install python-setuptools python-six python-requests python-fedfind python-wikitcms python-fedmsg-core python-resultsdb_api

A couple of dependencies are not available as packages, and must be checked out from git (to wherever you like):

    git clone https://github.com/os-autoinst/openQA-python-client.git
    git clone https://pagure.io/taskotron/resultsdb_conventions.git

You can install these dependencies system-wide by running `sudo python setup.py install` from the checkout, or alternatively, you can just symlink the library directory into the `fedora_openqa` directory. For instance, if you have the projects checked out like this:

    home/
        someuser/
            local/
                fedora_openqa/
                openQA-python-client/
                resultsdb_conventions/

Then you could do this, from `/home/someuser/local/fedora_openqa`:

    ln -s /home/someuser/local/resultsdb_conventions/resultsdb_conventions .
    ln -s /home/someuser/local/openQA-python-client/openqa_client .

You can then run `./fedora-openqa.py` from `/home/someuser/local/fedora_openqa` to use the CLI tool.

CLI usage
---------

Simple usages are:

    ./fedora-openqa.py compose https://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-Rawhide-20170214.n.0/compose/
    ./fedora-openqa.py update https://bodhi.fedoraproject.org/updates/FEDORA-2020-424d2b310e 32
    ./fedora-openqa.py report Fedora-Rawhide-20170214.n.0
    ./fedora-openqa.py report 1 2 3 4 5

The first schedules jobs for a particular compose, the second for a particular update. The third reports results for all jobs for a given compose. The third and fourth provides result reporting information for (respectively) a compose or some job IDs (the script will figure out whether you're passing it a compose ID or job ID(s)). Note that no actual reporting to Wikitcms or ResultsDB will be done unless `--wiki` or `--resultsdb` is also passed (instead, a list of passed Wikitcms test cases will be printed to the console).

See the command's help (and the help for the subcommands, `schedule` and `report`) for more details on usage.

Installation
------------

You can install the library and CLI systemwide if you choose to. After installing all the dependencies, just run `sudo python setup.py install`. You must install systemwide if you wish to use the fedora-messaging consumers to trigger jobs automatically.

Configuration
-------------

If the openQA server is deployed directly on the same system, openQA API access credentials should already be in place. If you are interacting with a remote openQA server, or one running in a container, you will need to configure these. First, visit `http://openqa.server(:PORT)/api_keys` (where `http://openqa.server` is the correct URL for the server) and authenticate as an administrator if necessary, and you should be able to generate an API key and secret. Then create a file `/etc/openqa/client.conf` or `~/.config/openqa/client.conf` with this content:

    [openqa.server(:PORT)]
    key = KEY
    secret = SECRET

By default the CLI will use the *first* openQA server specified in this config file. You can pass the `--openqa-hostname` argument to override this, but you must have a key and secret specified for the chosen server to create jobs on it (no key or secret are needed for result reporting, as this only requires querying of the openQA server).

If you wish to forward results to [Wikitcms](https://fedoraproject.org/wiki/Wikitcms), you must either authenticate interactively via a browser (which requires a graphical environment) periodically - each time you do this, a token will be kept for around a week, during which time reporting will work non-interactively, until one day you'll be prompted to authenticate again - or request a special non-expiring token from the wiki administrator. Please be careful before doing this, as usually only the official Fedora openQA systems should report results to Wikitcms. Ideally this should be a dedicated account for the purpose of reporting test results.

    sudo su
    mkdir /etc/fedora
    echo "fas_username fas_password" > /etc/fedora/credentials
    chmod 0600 /etc/fedora/credentials

This tool has its own configuration file which can be installed to `/etc/fedora-openqa/schedule.conf` or `~/.config/fedora-openqa/schedule.conf`. In this config file you can specify the locations of the wiki and ResultsDB instance that will be used when reporting results with `fedora-openqa report`; by default, results will be reported to the [staging wiki](https://stg.fedoraproject.org/wiki/) and to a ResultsDB instance running on localhost port 5001 (which is what you get if you follow the instructions to do a local deployment of ResultsDB for testing). A sample config file is provided as `sample-configs/schedule.conf.sample`, which you can copy into place and modify.

You can configure the set of images from each compose which will be downloaded and tested. For more details on this, see the comments in `sample-configs/images.json.sample`.

To run openQA jobs whenever a compose completes, and to report results to a ResultsDB instance and/or a wiki, you can use the fedora-messaging systemd service pattern.

**PLEASE NOTE** that there should never be more than one Fedora production Wiki or ResultsDB reporter enabled in the world, and both of these are run in the Fedora infrastructure, so please don't enable these on your own deployments. Reporting to your own wiki or ResultsDB instance for testing is of course fine.

First, you need to install one or more consumer configuration files to `/etc/fedora-messaging`. There are sample files provided in `sample-configs/` for Fedora production and staging configurations for the job scheduler, ResultsDB reporter and Wiki reporter:

    fedora_openqa_resultsdb_reporter.stg.toml
    fedora_openqa_resultsdb_reporter.toml
    fedora_openqa_scheduler.stg.toml
    fedora_openqa_scheduler.toml
    fedora_openqa_wiki_reporter.stg.toml
    fedora_openqa_wiki_reporter.toml

You can copy these into place and modify them as you like. You will at least need to replace the dummy UUID in each file (00000000-0000-0000-0000-000000000000) with a unique one generated by `uuidgen`, as explained in the comments. You may also change the authentication configuration and the settings in `consumer_config`. `openqa_hostname` is the openQA hostname to schedule jobs on (for the scheduler) or to retrieve the full job result details from (for the reporters). `openqa_baseurl` is the base URL to use for constructing links back to the results (for the reporters). For the Wiki reporter, `wiki_hostname` is the hostname of the wiki to send results to. For the ResultsDB reporter, `resultsdb_url` is the URL to send the results to (it should be the top-level API URL). For both reporter plugins, `do_report` configures whether to actually send the reports (if it is set false, the consumer will just log what it would have reported instead of actually reporting it).

You will also need to install the `fedora-messaging` package:

    sudo dnf install fedora-messaging

Once the configuration file(s) is/are in place, you can enable and start each consumer as a systemd service, for e.g.:

    sudo systemctl enable fm-consumer@fedora_openqa_scheduler
    sudo systemctl enable fedora_openqa_wiki_reporter.stg
    sudo systemctl start fm-consumer@fedora_openqa_scheduler
    sudo systemctl start fedora_openqa_wiki_reporter.stg

Once again, please please do **NOT** enable result reporter consumers unless you're really sure you should be doing it, and they are definitely not pointed at Fedora's production wiki or ResultsDB.

Also be aware that the result reporter consumer configurations are set to respond to jobs run in the official Fedora openQA deployments, not your own deployment. If you want to test the reporting workflow with jobs run on any other openQA instance, you will need to configure that instance such that fedmsgs emitted by openQA are forwarded to a fedora-messaging broker that the reporter consumers can subscribe to, and then configure the reporter consumers to subscribe to that broker instead. This is all somewhat outside the scope of this document. Usually, these consumers will only be used by the official Fedora openQA deployments.

# vim: set ts=8 et sw=4:

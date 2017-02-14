Fedora openQA scheduler and report tools
========================================

This repository contains a Python library (`fedora_openqa`) and CLI tool (`fedora-openqa`) that handle scheduling jobs in Fedora's instances ([production](https://openqa.fedoraproject.org) and [staging](https://openqa.stg.fedoraproject.org)) of [openQA](http://open.qa/). The library contains several fedmsg consumers which together form a fully automated pipeline for running tests in Fedora's official openQA instances. Jobs are scheduled in response to fedmsgs from release engineering. When a job completes, a fedmsg is emitted, and the 'reporter' consumers forward results to [Wikitcms](https://fedoraproject.org/wiki/Wikitcms) and [ResultsDB](https://fedoraproject.org/wiki/ResultsDB). The CLI allows manual triggering of jobs and reporting of results for testing with a local openQA deployment, or in case some issue in the automated pipeline requires manual intervention.

This repository does not contain the actual Fedora openQA tests. Those can be found [here](https://pagure.io/fedora-qa/os-autoinst-distri-fedora).

For general information on openQA in Fedora, including an overview of the system and how to install your own instance for testing, please see [the Fedora openQA wiki page](https://fedoraproject.org/wiki/openQA).

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

        ./fedora-openqa.py schedule https://kojipkgs.fedoraproject.org/compose/rawhide/Fedora-Rawhide-20170214.n.0/compose/
        ./fedora-openqa.py report Fedora-Rawhide-20170214.n.0
        ./fedora-openqa.py report 1 2 3 4 5

The first schedules jobs for a particular compose. The second reports results for all jobs for a given compose. The third reports results for the specified job IDs. Note that no actual reporting to Wikitcms or ResultsDB will be done unless `--wiki` or `--resultsdb` is also passed (instead, a list of passed Wikitcms test cases will be printed to the console).

See the command's help (and the help for the subcommands, `schedule` and `report`) for more details on usage.

Installation
------------

You can install the library and CLI systemwide if you choose to. After installing all the dependencies, just run `sudo python setup.py install`. You must install systemwide if you wish to use the fedmsg consumers to trigger jobs automatically.

Configuration
-------------

If the openQA server is deployed directly on the same system, openQA API access credentials should already be in place. If you are interacting with a remote openQA server, or one running in a container, you will need to configure these. First, visit `http://openqa.server(:PORT)/api_keys` (where `http://openqa.server` is the correct URL for the server) and authenticate as an administrator if necessary, and you should be able to generate an API key and secret. Then create a file `/etc/openqa/client.conf` or `~/.config/openqa/client.conf` with this content:

        [openqa.server(:PORT)]
        key = KEY
        secret = SECRET

By default the CLI will use the *first* openQA server specified in this config file. You can pass the `--openqa-hostname` argument to override this, but you must have a key and secret specified for the chosen server to create jobs on it (no key or secret are needed for result reporting, as this only requires querying of the openQA server).

If you wish to forward results to [Wikitcms](https://fedoraproject.org/wiki/Wikitcms), you must set up a python-wikitcms credentials file. This file contains a FAS username and password which will be used when reporting results to the wiki. See the `python-wikitcms` documentation for more details on this. Please be careful before doing this, as usually only the official Fedora openQA systems should report results to Wikitcms. Ideally this should be a dedicated account for the purpose of reporting test results.

        sudo su
        mkdir /etc/fedora
        echo "fas_username fas_password" > /etc/fedora/credentials
        chmod 0600 /etc/fedora/credentials

This tool has its own configuration file which can be installed to `/etc/fedora-openqa/schedule.conf` or `~/.config/fedora-openqa/schedule.conf`. In this config file you can specify the locations of the wiki and ResultsDB instance that will be used when reporting results with `fedora-openqa report`; by default, results will be reported to the [staging wiki](https://stg.fedoraproject.org/wiki/) and to a ResultsDB instance running on localhost port 5001 (which is what you get if you follow the instructions to do a local deployment of ResultsDB for testing). You can also specify the openQA, wiki and ResultsDB URLs / hostnames which will be used by the various fedmsg consumers. A sample config file is provided as `schedule.conf.sample`, which you can copy into place and modify.

You can configure the set of images from each compose which will be downloaded and tested. For more details on this, see the comments in `fedora_openqa/config.py`.

To run openQA jobs whenever a compose completes, you must install and enable fedmsg-hub. On Fedora:

        sudo dnf install fedmsg-hub
        sudo systemctl enable fedmsg-hub.service

Now enable the consumer. Create a file `/etc/fedmsg.d/fedora_openqa.py` with the contents:

        config = {
            'fedora_openqa.scheduler.prod.enabled': True,
        }

Now start fedmsg-hub (or restart it if it's already running):

        sudo systemctl start fedmsg-hub.service

In the Docker configuration you should probably set up the fedmsg consumer on the host system, ensuring you have set up the API credentials (as explained above). The fedmsg consumer will run as user 'fedmsg', so you need to give this user access to the openQA credentials:

        sudo chown root.fedmsg /etc/openqa/client.conf
        sudo chmod 0640 /etc/openqa/client.conf

To report results automatically when tests complete, you can use the various `reporter` consumers. There are six of these, three for reporting to Wikitcms and three for reporting to ResultsDB. For each system, one consumer listens out for production fedmsgs, one for staging fedmsgs, and one for 'dev' fedmsgs (which are what you get when replaying fedmsgs using `fedmsg-dg-replay`, commonly used for testing). Their configuration keys (to be added to the `/etc/fedmsg.d/fedora_openqa.py` file) are:

        fedora_openqa.reporter.resultsdb.prod.enabled
        fedora_openqa.reporter.resultsdb.stg.enabled
        fedora_openqa.reporter.resultsdb.test.enabled
        fedora_openqa.reporter.wiki.prod.enabled
        fedora_openqa.reporter.wiki.stg.enabled
        fedora_openqa.reporter.wiki.test.enabled

Usually, if you enable any of these consumers, they will respond to jobs run in the official Fedora openQA deployments, not your own deployment. If you want to test the reporting workflow with jobs run on any other openQA instance, you will need to configure that instance such that fedmsg emitted by openQA are published onto a fedmsg bus that the reporter consumers can subscribe to, and then configure the system where the reporter consumers run to lsiten to that bus. This is all somewhat outside the scope of this document. Usually, these consumers will only be used by the official Fedora openQA deployments.

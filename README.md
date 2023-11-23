# pNetwork v3 Monitoring

pNetwork v3 monitoring is a tool designed to monitor the pNetwork v3 decentralized network.

It allows users to perform essential checks and receive real-time feedback, aiding in the seamless
integration into various applications and existent monitoring systems.

---

## Installation

It can be run using `docker` or `pipenv`.

#### Using Docker

```bash
docker build -t pnetwork-monitoring-v3 .
docker run pnetwork-monitoring-v3 -c <checks>
```

#### Using Pipenv

```bash
pipenv install
pipenv run python main.py -c <checks>
```

---

# Configuration

In order to use the tool, you only need to edit the `config.py` file:

- `RPC_ENDPOINTS`: RPC endpoint url mapping (public or third-party, like QuickNode or Alchemy)
- `ipfs_url` and `ipfs_port`: an IPFS node in order to subscribe to the topic
- `pubsub_timeout`: how long the listener should run. Could be a value or a real-time stream (`0`)

---

## Usage

```
usage: main.py [-h] [-c CHECKS [CHECKS ...] | -a] [-v] [--version]
options:
  -h, --help            show this help message and exit
  -c CHECKS [CHECKS ...], --checks CHECKS [CHECKS ...]
                        choose the check/s to run
  -a, --all             run all checks
  -v, --verbose         print check's labels
  --version             print version and exit
```

#### Examples:

To run a single check (passing the key value or the full name):

```bash
pipenv run python main.py -c 5
- or
pipenv run python main.py -c max_ops_in_queue
```

```bash
docker run pnetwork-monitoring-v3 -c 5
- or
docker run pnetwork-monitoring-v3 -c max_ops_in_queue
```

To run multiple checks (passing the key values and/or the full names):

```bash
pipenv run python main.py -c 5 challenge_status 7
```

```bash
docker run pnetwork-monitoring-v3 -c 5 challenge_status 7
```

To run all the checks:

```bash
pipenv run python main.py -a
```

```bash
docker run pnetwork-monitoring-v3 -a
```

`-v` (`--verbose`) will also print the checks' labels.

A quick way to redirect only `stdout` on files, agents, etc. while maintaining the output:

```bash
pipenv run python main.py <args> 2>&1 | tee <log_file/stream>
```

```bash
docker run pnetwork-monitoring-v3 <args> 2>&1 | tee <log_file/stream>
```

Or just to redirect the output:

```bash
pipenv run python main.py <args> 2>&1 > <log_file/stream>
```

```bash
docker run pnetwork-monitoring-v3 <args> 2>&1 > <log_file/stream>
```

The tool will print the results splitting errors to `stderr` and results to `stdout`.
This separation allows users to easily integrate the tool into their favorite monitoring tools
or agents by writing a wrapper.

All the results are `json` formatted.

#### Enabled checks

```
1. challenge_period_duration
2. challenge_status
3. components_balances

# Rm double 4.
4. 4.inactive_actors_by_epoch
5. max_ops_in_queue
6. nr_of_ops_in_queue
7. operation_cancelled
8. queue_op_after_user_op
9. queue_operations_with_threshold
10. slashed_actors
11. user_ops
12. ipfs_subpub_pnetwork_topics
```

---

# Examples

Simple run via `docker` for a single check:

```bash
$ docker run pnetwork-monitoring -c 5

{
    "title": "max_ops_in_queue",
    "timestamp": 1698686055,
    "chain": "bsc",
    "max_ops_in_queue": 10
}
{
    "title": "max_ops_in_queue",
    "timestamp": 1698686056,
    "chain": "goerli",
    "max_ops_in_queue": 10
}
{
    "title": "max_ops_in_queue",
    "timestamp": 1698686057,
    "chain": "polygon",
    "max_ops_in_queue": 10
}
```

Simple run via `pipenv` with multiple checks and `verbose`:

```bash
$ pipenv run python main.py -v -c 1 5

[+] Check `challenge_period_duration` (1):

{
    "title": "challenge_period_duration",
    "timestamp": 1698686721,
    "chain": "bsc",
    "challenge_period_duration": 600
}
{
    "title": "challenge_period_duration",
    "timestamp": 1698686722,
    "chain": "goerli",
    "challenge_period_duration": 600
}
{
    "title": "challenge_period_duration",
    "timestamp": 1698686723,
    "chain": "polygon",
    "challenge_period_duration": 608
}

 ##########################################


[+] Check `max_ops_in_queue` (5):

{
    "title": "max_ops_in_queue",
    "timestamp": 1698686727,
    "chain": "bsc",
    "max_ops_in_queue": 10
}
{
    "title": "max_ops_in_queue",
    "timestamp": 1698686728,
    "chain": "goerli",
    "max_ops_in_queue": 10
}
{
    "title": "max_ops_in_queue",
    "timestamp": 1698686729,
    "chain": "polygon",
    "max_ops_in_queue": 10
}

 ##########################################

```

Run via `pipenv` for a single check, this time redirecting only `stdout` on `test_log`:

```bash
$ pipenv run python main.py -c 1 2>&1 > test_log
$ cat test_log
{
    "title": "challenge_period_duration",
    "timestamp": 1698687084,
    "chain": "bsc",
    "challenge_period_duration": 600
}
{
    "title": "challenge_period_duration",
    "timestamp": 1698687085,
    "chain": "goerli",
    "challenge_period_duration": 600
}
{
    "title": "challenge_period_duration",
    "timestamp": 1698687086,
    "chain": "polygon",
    "challenge_period_duration": 608
}

```

---

# Contributing

We welcome contributions from the open-source community.

---

# License

This project is licensed under
the [MIT License](https://github.com/pnetwork-association/pnetwork-v3-monorepo/blob/master/LICENSE).

---

# Disclaimer

Please note that the project is under active development, and the structure and implementation are subject to change.

---

# Contact

For any questions, feedback, or discussions, please open an issue on this repository or reach out to us at [our contact email](mailto:admin@p.network).

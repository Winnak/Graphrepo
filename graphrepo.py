#!/usr/bin/env python3
import subprocess
import sys
import datetime as dt
from os import path as os_path, getcwd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def main(path: str) -> None:
    log_lines = get_log_lines(path)
    commits = parse_commits(log_lines, path=path)
    commit_len = len(commits)

    if commit_len == 0:
        return

    added = [0] * commit_len
    rmved = [0] * commit_len
    total = [0] * commit_len
    dates = [0] * commit_len
    dates[0] = commits[0][1]
    added[0] = commits[0][4]
    rmved[0] = commits[0][5]
    total[0] = added[0] - rmved[0]

    for idx in range(1, commit_len):
        commit = commits[idx]
        added[idx] += added[idx - 1] + commit[4]
        rmved[idx] += rmved[idx - 1] + commit[5]
        total[idx] += added[idx] - rmved[idx]
        dates[idx] = commit[1]

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
    # plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.subplot(211)
    plt.plot(dates, added, color="g", label="added")
    plt.plot(dates, rmved, color="r", label="removed")
    plt.legend(loc="upper left")
    plt.xlabel("Date")
    plt.ylabel("Changes (Cumulative)")

    plt.subplot(212)
    plt.plot(dates, total, color="b", label="total")
    plt.legend(loc="upper left")
    plt.ylabel("Lines of code")
    plt.xlabel("Date")
    plt.gcf().autofmt_xdate()
    plt.show()

def parse_commits(log_lines: [str], **kwargs) -> [(str, str, str, int, int)]:
    prefix = kwargs.get("prefix", "")
    path = kwargs.get("path", PATH)

    if not log_lines:
        print(prefix, "No commits found", file=sys.stderr)
        return []

    commits = list()
    print(prefix, "Parsing", len(log_lines), "commits ...")

    prev_commit = parse_log_line(log_lines[0])
    root_commit_proc = subprocess.run(
        ["git", "diff-tree", "--numstat", "--root", prev_commit[0]],
		stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # capture_output=True, # for Python3.7
        cwd=path)
    prev_commit += parse_diff_response(root_commit_proc)
    commits.append(prev_commit)

    x_counter = 0

    for log_line in log_lines[1:]:
        commit = parse_log_line(log_line)
        diff = get_diff(path, commit, prev_commit)
        commit += parse_diff_response(diff)
        prev_commit = commit
        commits.append(commit)
        x_counter += 1
        if x_counter % 100 == 0:
            print(prefix, "Parsed", x_counter, "so far")

    return commits

def parse_diff_response(diff_proc) -> (int, int):
    diff_text = str(diff_proc.stdout, encoding="utf8").splitlines()
    added = 0
    removed = 0
    for diffline in diff_text:
        split = diffline.split("\t")
        if len(split) != 3:
            continue
        [newa, newr, _] = split
        if newa == "-" or newr == "-":
            continue
        added += int(newa)
        removed += int(newr)
    return (added, removed)

def get_log_lines(path: str) -> [str]:
    log_process = subprocess.run(
        ["git", "log", "--format=%H%cI;%ce;%s", "--reverse"],
        # capture_output=True, # for Python3.7
		stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=path)

    if log_process.returncode != 0:
        print("Failed to run: ",
              str(log_process.stderr, encoding="utf8"),
              file=sys.stderr)
        return []

    return str(log_process.stdout, encoding="utf8").splitlines()

def parse_log_line(line: str) -> (str, str, str, str, int, int):
    result = line[40:].split(";", 2)
    return (line[:40], parse_time(result[0]), result[1], result[2])

def parse_time(timestamp: str):
    temp = timestamp[:22] + timestamp[23:] # why not the isoformat?
    return dt.datetime.strptime(temp, "%Y-%m-%dT%H:%M:%S%z")

def get_diff(path: str, current: str, previous: str) -> str:
    result = subprocess.run(
        ["git", "diff-tree", "--numstat", previous[0], current[0]],
        # capture_output=True, # for Python3.7
		stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=path)
    result.check_returncode()
    return result


if __name__ == "__main__":
    PATH = getcwd()
    if len(sys.argv) > 1:
        PATH = os_path.abspath(sys.argv[1])
        if not os_path.isdir(PATH):
            print("Not a valid path", PATH, file=sys.stderr)
            exit(1)
    main(PATH)

#!/usr/bin/env python3


import argparse
import csv
import sys
from tabulate import tabulate
import io

# number of parameters of execution
__PYCO_PROC_PARAMS_NUM = 1

def proc_res(fd, args):
    """proc_res(fd, args) -> _|_

    processes results of pycobench from file descriptor 'fd' using command line
    arguments 'args'
"""
    reader = csv.reader(
        fd, delimiter=';', quotechar='"',
        doublequote=False, quoting=csv.QUOTE_MINIMAL)

    engines = list()
    engines_outs = dict()
    results = dict()
    for row in reader:
        assert len(row) >= 1 + 1 + __PYCO_PROC_PARAMS_NUM  # status + engine name + params
        status, eng = row[0], row[1]
        params = tuple(row[2:(__PYCO_PROC_PARAMS_NUM+2)])
        row_tail = row[(__PYCO_PROC_PARAMS_NUM+2):]
        if params not in results:
            results[params] = dict()
        if eng not in engines:
            engines.append(eng)
            engines_outs[eng] = ["result"]

        # we don't have some results twice
        assert eng not in results[params]

        if status == 'finished':
            retcode, out, err, runtime = row_tail[0], row_tail[1], \
                                         row_tail[2], row_tail[3]

            eng_res = dict()
            eng_res["runtime"] = runtime
            eng_res["retcode"] = retcode
            eng_res["error"] = err
            eng_res["output"] = dict()

            out_lines = [out]
            for line in out_lines:
                spl = line.split(':', 1)
                if len(spl) != 2:  # jump over lines not in the format
                    continue
                name, val = spl[0], spl[1]
                if name != 'result':
                    # sys.stderr.write(f"Warning: line in wrong format: {spl}\n")
                    continue
                eng_res["output"][name] = val

            results[params][eng] = eng_res

        if status == 'error':
            results[params][eng] = "ERR"

        if status == 'timeout':
            results[params][eng] = "TO"

    list_ptrns = list()
    for bench in results:
        all_engs = True
        ls = list(bench)
        for eng in engines:
            out_len = len(engines_outs[eng]) + 1    # +1 = time
            if eng in results[bench]:
                bench_res = results[bench][eng]
                if bench_res == "ERR":
                    for i in range(out_len):
                        ls.append("ERR")
                elif bench_res == "TO":
                    for i in range(out_len):
                        ls.append("TO")
                else:
                    assert type(bench_res) == dict
                    assert "output" in bench_res

                    ls.append(bench_res["runtime"])
                    for out in engines_outs[eng]:
                        if out in bench_res["output"]:
                            ls.append(bench_res["output"][out])
                        else:
                            # sys.stderr.write("Warning: in {} and {}: "
                            #     "element {} not in {}\n".format(bench, eng,
                            #     out, bench_res["output"]))
                            ls.append("MISSING")
                            # assert False
            else:
                all_engs = False
                for i in range(out_len):
                    ls.append("MISSING")

        # prepend with status of the benchmark
        if args.tick:
            if all_engs:
                ls = ["T"] + ls
            else:
                ls = ["F"] + ls

        list_ptrns.append(ls)

    header = list()
    if args.tick:
        header += ["T"]

    header += ['name']
    for eng in engines:
        header += [eng + "-runtime"]
        for out in engines_outs[eng]:
            header += [eng + "-result"]

    fmt = "text"
    if args.csv:
        fmt = "csv"
    if args.text:
        fmt = "text"
    if args.html:
        fmt = "html"

    if fmt == 'html':
        return tabulate(list_ptrns, header, tablefmt='html')
    elif fmt == 'text':
        return tabulate(list_ptrns, header, tablefmt='text')
    elif fmt == 'csv':
        output = io.StringIO()
        writer = csv.writer(
            output, delimiter=';', quotechar='"', escapechar='\\',
            doublequote=False, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        writer.writerows(list_ptrns)
        return output.getvalue()
    else:
        raise Exception('Invalid output format: "{}"'.format(fmt))
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''proc_results.py - \
Processes results of benchmarks from pycobench''')
    parser.add_argument('results', metavar='result-file', nargs='?',
                        help='file with results (output of pycobench);'
                             'if not provided stdin is used')
    parser.add_argument('--csv', action="store_true",
                        help='output in CSV')
    parser.add_argument('--text', action="store_true",
                        help='output in text')
    parser.add_argument('--html', action="store_true",
                        help='output in HTML')
    parser.add_argument('--tick', action="store_true",
                        help='tick finished benchmarks (usable for filtering)')
    args = parser.parse_args()

    if args.results:
        fd = open(args.results, "r")
    else:
        fd = sys.stdin

    print(proc_res(fd, args, sys.stdout))
    if args.results:
        fd.close()

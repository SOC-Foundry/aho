with open("src/aho/cli.py", "r") as f:
    lines = f.readlines()

out = []
for line in lines:
    if line.strip() == "args = p.parse_args()":
        out.append('    pcouncil = sub.add_parser("council", help="Council visibility and status")\n')
        out.append('    pcouncil_subs = pcouncil.add_subparsers(dest="council_cmd")\n')
        out.append('    pc_status = pcouncil_subs.add_parser("status", help="Show operational state of council components")\n')
        out.append('    pc_status.add_argument("--json", action="store_true", help="Output machine-readable JSON")\n')
        out.append('    pc_status.add_argument("--member", help="Detail on one member")\n')
        out.append('    pc_status.add_argument("--verbose", action="store_true", help="Include G083 scan summary and routing activity")\n\n')
        out.append(line)
    elif line.strip() == 'elif args.cmd in ("eval", "registry"):':
        out.append('    elif args.cmd == "council":\n')
        out.append('        if args.council_cmd == "status":\n')
        out.append('            from aho.council.status import collect_status, format_human, format_json\n')
        out.append('            status = collect_status()\n')
        out.append('            if args.json or args.member:\n')
        out.append('                print(format_json(status, member=args.member))\n')
        out.append('            else:\n')
        out.append('                print(format_human(status, verbose=args.verbose))\n')
        out.append('        else:\n')
        out.append('            pcouncil.print_help()\n')
        out.append(line)
    elif "for name, (status, msg) in results.items():" in line:
        indent = line[:len(line) - len(line.lstrip())]
        out.append(f"{indent}for name, result_tuple in results.items():\n")
        out.append(f"{indent}    status, msg = result_tuple[0], result_tuple[1]\n")
    else:
        out.append(line)

with open("src/aho/cli.py", "w") as f:
    f.writelines(out)

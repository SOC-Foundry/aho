import re

with open("src/aho/cli.py", "r") as f:
    content = f.read()

# Re-apply W6 logic (lost via checkout)
parser_injection = """
    pcouncil = sub.add_parser("council", help="Council visibility and status")
    pcouncil_subs = pcouncil.add_subparsers(dest="council_cmd")
    pc_status = pcouncil_subs.add_parser("status", help="Show operational state of council components")
    pc_status.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    pc_status.add_argument("--member", help="Detail on one member")
    pc_status.add_argument("--verbose", action="store_true", help="Include G083 scan summary and routing activity")

    args = p.parse_args()"""

content = content.replace("    args = p.parse_args()", parser_injection)

handler_injection = """    elif args.cmd == "council":
        if args.council_cmd == "status":
            from aho.council.status import collect_status, format_human, format_json
            status = collect_status()
            if args.json or args.member:
                print(format_json(status, member=args.member))
            else:
                print(format_human(status, verbose=args.verbose))
        else:
            pcouncil.print_help()
    elif args.cmd in ("eval", "registry"):"""

content = content.replace('    elif args.cmd in ("eval", "registry"):', handler_injection)

# Fix postflight unpack
content = re.sub(r'for name, \(status, msg\) in results\.items\(\):', r'for name, result_tuple in results.items():\n                status, msg = result_tuple[0], result_tuple[1]', content)

with open("src/aho/cli.py", "w") as f:
    f.write(content)

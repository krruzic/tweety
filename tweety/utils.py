def walk_dict(d, depth=0):
    if isinstance(d, list):
        for i, v in enumerate(d):
            print("  " * depth + "[%d]" % i)
            walk_dict(v, depth + 1)
    if isinstance(d, dict):
        for k, v in sorted(d.items(), key=lambda x: x[0]):
            if isinstance(v, dict):
                print("  " * depth + "%s" % k)
                walk_dict(v, depth + 1)
            if isinstance(d, list):
                for i, v in enumerate(d):
                    print("  " * depth + "[%d]" % i)
                    walk_dict(v, depth + 1)
            else:
                print("  " * depth + "%s" % k)

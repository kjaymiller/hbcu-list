import pandas as pd

hbcus = pd.read_html('HBCU_LIST.html')[0]

with open('README.md', 'w') as fp:
    fp.write("# HBCUs in the United States")

    for name in sorted(hbcus['State/Territory'].unique()):
        fp.write(f"\n ## {name}\n---\n")
        schools = hbcus[hbcus['State/Territory'] == name].School.values
        fp.write('\n\n'.join(schools))

    fp.write("\nsource: <https://en.wikipedia.org/wiki/List_of_historically_black_colleges_and_universities>")


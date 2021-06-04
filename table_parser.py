import pathlib 
import pandas as pd
import frontmatter
from slugify import slugify
from frontmatter.default_handlers import JSONHandler

hbcus = pd.read_html('HBCU_LIST.html')[0]
hbcus.rename(columns={"Regionally accredited[3]":"Regionally acredited"}, inplace=True)

def gen_slug_link(school):
    school_name = school
    link = slugify(school_name)

    return f"[{school_name}](/pages/{link})"

def gen_readme():
    with open('README.md', 'w') as fp:
        fp.write("# HBCUs in the United States")

        for name in sorted(hbcus['State/Territory'].unique()):
            fp.write(f"\n ## {name}\n\n")
            schools = map(gen_slug_link, hbcus[hbcus['State/Territory'] == name].School.values)
            fp.write('\n\n'.join(list(schools)))

        fp.write("\nsource: <https://en.wikipedia.org/wiki/List_of_historically_black_colleges_and_universities>")

def build_pages():
    hbcus.set_index("School")
    hbcu_json = hbcus.to_dict(orient="records")

    for row in hbcu_json:
        f_meta= []

        for name, val in row.items():
            if name != "Comment":
                f_meta.append(f"{name}: {val}")

        ftext = '\n'.join(f_meta)

        filepath = pathlib.Path(slugify(row['School'])).with_suffix('.md')
        page = pathlib.Path('pages').joinpath(filepath)

        page.write_text(f"""---
{ftext}
---
{row['Comment']}""")

        

if __name__ == "__main__":
    gen_readme()
